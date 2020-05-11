#  License: MIT
#  Copyright (c) 2020 - Pizarra
#
import enum
import logging
import math
import os
import re
import subprocess
import time
from datetime import timedelta

import redis
import rule_engine
from flask import current_app
from rq import Connection, Queue

from app import db
from app.base.ssh_client import RemoteClient
from app.base.util import remove_comments


class RequestStatus(enum.Enum):
    CREATED = 0
    VERIFYING = 1
    COMPILING = 2
    DEPLOYING = 3
    QUEUED = 4
    RUNNING = 5
    CANCELED = 6
    ERROR = 7
    TIMEWALL = 8
    FINISHED = 9

    @property
    def label(self):
        """
        Dictionary to map enum to Bootstrap labels
        """
        label_dict = {RequestStatus.COMPILING: 'label-info', RequestStatus.DEPLOYING: 'label-info',
                      RequestStatus.RUNNING: 'label-primary', RequestStatus.FINISHED: 'label-success',
                      RequestStatus.CANCELED: 'label-warning', RequestStatus.ERROR: 'label-danger',
                      RequestStatus.TIMEWALL: 'label-warning'}
        return label_dict[self] if self in label_dict else 'label-default'


class LocalTask:

    def __init__(self, user_request):
        self.user_request = user_request
        self.output = ''
        self.binary_file_location = ''
        self.return_code = 0
        self.run_time = 0.0
        self.points_earned = 0
        # defines the function to be executed in next step
        self.task_process = {
            RequestStatus.CREATED: self.not_contains_malicious_content,
            RequestStatus.VERIFYING: self.compile,
            RequestStatus.COMPILING: self.run
        }

    def __str__(self):
        return '{} -> {}'.format(self.user_request.id, self.user_request.status)

    def get_task_step(self):
        return self.task_process.get(self.user_request.status)

    @property
    def is_task_completed(self):
        completed_task_status = [RequestStatus.CANCELED, RequestStatus.ERROR, RequestStatus.TIMEWALL,
                                 RequestStatus.FINISHED]

        return self.user_request.status in completed_task_status

    @property
    def rule_engine_attributes(self):
        return {
            'request': self.user_request.__dict__,
            'user': self.user_request.user.__dict__,
            'assignment': self.user_request.assignment.__dict__
        }

    def process(self):
        """
        process the task request
        """
        step_result = True
        while step_result and not self.is_task_completed:
            logging.info('Task: {} -> Status {}'.format(self.user_request.id, self.user_request.status))
            f = self.get_task_step()
            step_result = f()

        if self.is_task_completed:
            # check if user won any badge, this can happen even if we were timewalled or an error was thrown
            self.assign_badges()
            self.update_user_quota_and_points()
            # update request one last time to set points_earned to request
            self.update_request()

        return True

    def not_contains_malicious_content(self):
        """
        verifies code for malicious content (taken from Tablón)
        """
        # update status
        self.update_request(RequestStatus.VERIFYING)

        # open file and check for forbidden code
        with current_app.open_resource(self.user_request.file_location, mode='r') as f:
            file_content = remove_comments(f.read())
            for i, line in enumerate(file_content.split('\n')):
                # check if line contains any forbidden code
                if any(re.search(fc, line) for fc in current_app.config['FORBIDDEN_CODE']):
                    self.update_request(RequestStatus.ERROR)
                    self.output = 'Found forbidden code at line {}\n\n{}'.format(i + 1, line)
                    return False

        return True

    def compile(self):
        """
        compiles the source and returns if it was successful
        """
        self.update_request(RequestStatus.COMPILING)
        file_location = os.path.join(os.getcwd(), 'app', self.user_request.file_location)
        self.binary_file_location = os.path.splitext(file_location)[0]

        # localhost compile -> gcc-9 -fopenmp omp_hello.c -o hello
        return_code, elapsed_time = self.run_process(
            [current_app.config['COMPILER'], '-fopenmp', file_location, '-o', self.binary_file_location], False)

        if return_code != 0:
            self.update_request(RequestStatus.ERROR)
            return False

        return True

    def run(self):
        try:
            return self.execute()
        except subprocess.TimeoutExpired:
            self.timewalled()

        return False

    def execute(self):
        """
        runs compiled binary
        """
        self.update_request(RequestStatus.RUNNING)

        # TODO run process with inputs and expected outputs
        self.run_process([self.binary_file_location])

        # sum assignment points
        self.points_earned += self.user_request.assignment.points
        # mark as finished :)
        self.update_request(RequestStatus.FINISHED)

        return True

    def timewalled(self):
        """
        marks a request as TIMEWALL
        """
        self.run_time = self.user_request.max_execution_time
        self.points_earned += current_app.config['TIMEWALL_PENALTY']
        self.update_request(RequestStatus.TIMEWALL)

    def assign_badges(self):
        """
        checks for badges that can be assigned when a Request finishes successfully
        """
        for badge in self.user_request.assignment.badges:
            if badge.rule is not None and badge.points is not None and badge not in self.user_request.user.badges:
                rule = rule_engine.Rule(badge.rule)
                if rule.matches(self.rule_engine_attributes):
                    self.points_earned += badge.points
                    user = self.user_request.user
                    user.badges.append(badge)
                    db.session.add(user)
                    db.session.commit()
                    print('{} matched'.format(badge.name))

    def update_user_quota_and_points(self):
        """
        adds the given points to the user account and to the Task
        """
        # points for the user account
        user = self.user_request.user
        user.quota_used += math.ceil(self.run_time)  # always round up, even if time was less than 1 second
        user.points = max(user.points + self.points_earned, 0)  # points can't be negative
        db.session.add(user)
        db.session.commit()

    def run_process(self, args: list, update_run_time=True):
        """
        runs a subprocess and updates the return code and output, returns code and execution time
        if update_run_time then it will add execution time to pool of used time
        """
        timeout = self.user_request.max_execution_time - self.run_time
        # run process and take timing
        start = time.time()
        output = subprocess.run(args, stdout=subprocess.PIPE, universal_newlines=True, timeout=timeout)
        elapsed_time = time.time() - start

        try:
            output.check_returncode()
            self.output = output.stdout
        except subprocess.CalledProcessError:
            self.output = 'Unable to compile file.'

        self.return_code = output.returncode
        self.run_time = (self.run_time + elapsed_time) if update_run_time else self.run_time

        return output.returncode, elapsed_time

    def update_request(self, status=None):
        """
        update status of Request
        """
        self.user_request.status = self.user_request.status if status is None else status
        self.user_request.output = self.output
        self.user_request.run_time = self.run_time
        self.user_request.points = self.points_earned

        db.session.add(self.user_request)
        db.session.commit()


class KahanTask(LocalTask):

    def __init__(self, user_request):
        super().__init__(user_request)
        self.task_process = {
            RequestStatus.CREATED: self.not_contains_malicious_content,
            RequestStatus.VERIFYING: self.compile,
            RequestStatus.COMPILING: self.deploy,
            RequestStatus.QUEUED: self.check_queue
        }

    def deploy(self):
        self.update_request(RequestStatus.DEPLOYING)
        remote = RemoteClient()
        files = list(map(lambda attachment: os.path.join(current_app.config['BASE_DIR'], attachment.file_location),
                         self.user_request.assignment.attachments))
        remote.bulk_upload(files)

        # TODO if OK
        self.update_request(RequestStatus.QUEUED)
        return True

    def check_queue(self):
        # TODO check queue if has to check it on the future we requeue the task
        requeue_task(self)
        return False


def process_task(task) -> bool:
    """
    process a task and returns the result
    """
    return task.process()


def create_task(user_request) -> str:
    """
    creates and enqueues a task from pizarra to be executed by a worker and returns task id
    """
    with Connection(redis.from_url(current_app.config["RQ_DASHBOARD_REDIS_URL"])):
        q = Queue(name=user_request.assignment.queue)
        task = q.enqueue(process_task, KahanTask(user_request))
        return task.get_id()


def requeue_task(task) -> str:
    """
    enqueues a task to be executed in the future
    """
    with Connection(redis.from_url(current_app.config["RQ_DASHBOARD_REDIS_URL"])):
        q = Queue(name=task.user_request.assignment.queue)
        task = q.enqueue_in(timedelta(seconds=10), process_task, task)
        return task.get_id()
