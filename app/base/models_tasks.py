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

import lizard
import redis
import rule_engine
from flask import current_app
from rq import Connection, Queue

from app import db
from app.base.ssh_client import RemoteClient
from app.base.util import remove_comments


class StepResult(enum.Enum):
    START = 0
    OK = 1
    NOK = 2
    WAIT = 3
    END = 4


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
    KO = 10
    UNHANDLED_ERROR = 99

    @property
    def label(self):
        """
        Dictionary to map enum to Bootstrap labels
        """
        label_dict = {RequestStatus.COMPILING: 'label-info', RequestStatus.DEPLOYING: 'label-info',
                      RequestStatus.RUNNING: 'label-primary', RequestStatus.FINISHED: 'label-success',
                      RequestStatus.CANCELED: 'label-warning', RequestStatus.ERROR: 'label-danger',
                      RequestStatus.KO: 'label-danger', RequestStatus.TIMEWALL: 'label-warning'}
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
            RequestStatus.CREATED: self.__not_contains_malicious_content,
            RequestStatus.VERIFYING: self.compile,
            RequestStatus.COMPILING: self.run
        }

    def __str__(self):
        return 'Task {} -> {}'.format(self.user_request.id, self.user_request.status)

    def get_task_step(self):
        return self.task_process[self.user_request.status]

    @property
    def is_task_completed(self):
        completed_task_status = [RequestStatus.CANCELED, RequestStatus.ERROR, RequestStatus.TIMEWALL,
                                 RequestStatus.FINISHED, RequestStatus.UNHANDLED_ERROR]

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

    def start(self):
        """
        dummy business process step
        """
        return StepResult.OK

    def verify(self):
        return StepResult.OK if (
                self.__not_contains_malicious_content() and self.__static_code_analysis()) else StepResult.NOK

    def __not_contains_malicious_content(self):
        """
        verifies code for malicious content (taken from Tablón)
        """
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

    def __static_code_analysis(self):
        """
        runs lizard static code analysis
        """
        try:
            self.user_request.code_analysis = analyze_code(
                os.path.join(current_app.config['BASE_DIR'], 'app', self.user_request.file_location))
        except:
            return StepResult.NOK
        return StepResult.OK

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

        return StepResult.OK if return_code == 0 else StepResult.OK

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

    def check_results(self):
        return True

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

    def run_process(self, args: list, update_run_time=False):
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

    def end(self):
        """
        task was completed, update it for points, badges and more
        """
        # check if user won any badge, this can happen even if we were timewalled or an error was thrown
        self.assign_badges()
        self.update_user_quota_and_points()
        self.user_request.update_leaderboard()

        return StepResult.END

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
            RequestStatus.CREATED: {
                'f': self.start,
                'steps': {
                    StepResult.OK: RequestStatus.VERIFYING,
                }
            },
            RequestStatus.VERIFYING: {
                'f': self.verify,
                'steps': {
                    StepResult.OK: RequestStatus.COMPILING,
                    StepResult.NOK: RequestStatus.ERROR
                }
            },
            RequestStatus.COMPILING: {
                'f': self.compile,
                'steps': {
                    StepResult.OK: RequestStatus.DEPLOYING,
                    StepResult.NOK: RequestStatus.ERROR
                }
            },
            RequestStatus.DEPLOYING: {
                'f': self.deploy,
                'steps': {
                    StepResult.OK: RequestStatus.QUEUED,
                    StepResult.NOK: RequestStatus.ERROR
                }
            },
            RequestStatus.QUEUED: {
                'f': self.check_queue,
                'steps': {
                    StepResult.OK: RequestStatus.FINISHED,
                    StepResult.NOK: RequestStatus.KO
                }
            },
            RequestStatus.RUNNING: {
                'f': self.check_queue,
                'steps': {
                    StepResult.OK: RequestStatus.FINISHED,
                    StepResult.NOK: RequestStatus.KO
                }
            },
            RequestStatus.ERROR: {
                'f': self.end,
                'steps': {
                    StepResult.OK: RequestStatus.ERROR
                }
            },
            RequestStatus.TIMEWALL: {
                'f': self.end,
                'steps': {
                    StepResult.OK: RequestStatus.TIMEWALL
                }
            },
            RequestStatus.FINISHED: {
                'f': self.end,
                'steps': {
                    StepResult.OK: RequestStatus.FINISHED
                }
            },
            RequestStatus.KO: {
                'f': self.end,
                'steps': {
                    StepResult.OK: RequestStatus.KO
                }
            }
        }

    @property
    def remote_directory(self):
        return os.path.join(current_app.config['REMOTE_PATH'], str(self.user_request.id))

    def process(self):
        """
        process the task request step by step until the task is enqueued again or it finishes
        """
        step_result = StepResult.OK
        while step_result != StepResult.END:
            logging.info(self)
            step = self.get_task_step()
            f = step['f']
            try:
                step_result = f()
            except Exception as e:
                self.user_request.output = str(e)
                self.update_request(RequestStatus.UNHANDLED_ERROR)
                break

            if step_result == StepResult.WAIT:
                requeue_task(self)
                break

            if step_result == StepResult.END:
                break

            self.update_request(step['steps'][step_result])

        return True

    def compile(self) -> StepResult:
        remote = RemoteClient.Instance()
        # create request directory
        remote.execute_commands(['mkdir -p ' + self.remote_directory])
        # assignment files
        files = list(map(lambda attachment: os.path.join(current_app.config['BASE_DIR'], attachment.file_location),
                         self.user_request.assignment.attachments))
        # append cputils.c
        files.append(os.path.join(current_app.config['BASE_DIR'], 'app/data/cputils.h'))
        # append source code to compile
        files.append(os.path.join(current_app.config['BASE_DIR'], 'app', self.user_request.file_location))
        # upload all files
        remote.bulk_upload(files, self.remote_directory)
        # execute all commands at once
        concat_commands = ' && '.join(['cd ' + self.remote_directory, 'mv *.c primos.c', 'make'])
        remote.execute_commands([concat_commands])

        return StepResult.OK

    def deploy(self):
        remote = RemoteClient.Instance()
        output = remote.execute_commands_in_directory(self.remote_directory, ['qsub script.sh'])
        kahan_queue_id = get_kahan_queue_id(output)
        if kahan_queue_id is None:
            return StepResult.NOK

        self.user_request.kahan_id = kahan_queue_id
        return StepResult.OK

    def check_queue(self):
        remote = RemoteClient.Instance()
        # check if finish
        output = remote.execute_commands(['qstat |grep ' + self.user_request.kahan_id])
        request_status = get_kahan_queue_status(output)
        if request_status == RequestStatus.QUEUED or request_status == RequestStatus.RUNNING:
            # if the status change, we update it, eg: from Q to R
            if request_status != self.user_request.status:
                self.update_request(request_status)
            # requeue task
            return StepResult.WAIT

        # obtain output
        output = remote.execute_commands_in_directory(self.remote_directory, ['cat script.sh.e*', 'cat script.sh.o*'])
        self.output = '\n'.join(output)
        # find result and time
        self.run_time = get_kahan_time(self.output)
        if check_kahan_result(self.user_request.assignment.expected_result, self.output):
            self.points_earned += self.user_request.assignment.points
            return StepResult.OK
            
        self.points_earned += current_app.config['KO_PENALTY']
        return StepResult.NOK


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
        rq_task = q.enqueue(process_task, KahanTask(user_request))
        return rq_task.get_id()


def requeue_task(task):
    """
    enqueues a task to be executed in the future
    """
    with Connection(redis.from_url(current_app.config["RQ_DASHBOARD_REDIS_URL"])):
        q = Queue(name=task.user_request.assignment.queue)
        rq_task = q.enqueue_in(timedelta(seconds=10), process_task, task)
        task.user_request.task_id = rq_task.get_id()
        db.session.add(task.user_request)
        db.session.commit()


def analyze_code(file_location: str) -> dict:
    """
    execute lizard static code analyzer and returns result
    """
    code_analysis = lizard.analyze_file(file_location)
    return code_analysis.function_list[0].__dict__ if len(code_analysis.function_list) > 0 else None


def get_kahan_queue_id(output: list):
    """
    obtains the kahan queue id from the output of the qsub command
    :param output list with all the output lines from kahan server
    """
    return output[0] if len(output) > 0 and output[0].isdigit() else None


def get_kahan_queue_status(output: list):
    """
    checks and returns the status of the queue
    Q -> queue
    R -> running
    ? ->
    """
    if len(output) > 0:
        # eg: ['260354', 'script.sh', 'nimar3', '0', 'R', 'cpa']
        output = output[0].split()[4]
        return RequestStatus.QUEUED if output == 'Q' else RequestStatus.RUNNING
    return None


def check_kahan_result(expected_result: str, output: str):
    regex_result = r'Result: (.+).'
    result = re.search(regex_result, output)
    return True if result is not None and result.group(1) == expected_result else False


def get_kahan_time(output: str) -> float:
    """
    returns time spent on kahan, if not found it will return 5 minutes as expected wall time
    :param output to search for execution time
    """
    regex_time = 'Time: (.*)\n'
    result = re.search(regex_time, output)
    return float(result.group(1)) if result is not None else float(300.0)
