#  License: MIT
#  Copyright (c) 2020 - Pizarra
#
import enum
import os
import re
import subprocess
import time

from flask import current_app

from app import db
from app.base.util import remove_comments


class RequestStatus(enum.Enum):
    CREATED = 0
    VERIFYING = 1
    COMPILING = 2
    QUEUED = 3
    DEPLOYING = 4
    WAITING = 5
    RUNNING = 6
    FINISHED = 7
    CANCELED = 8
    ERROR = 9
    TIMEWALL = 10

    @property
    def label(self):
        """
        Dictionary to map enum to Bootstrap labels
        """
        label_dict = {RequestStatus.COMPILING: 'label-info', RequestStatus.DEPLOYING: 'label-info',
                      RequestStatus.WAITING: 'label-info', RequestStatus.RUNNING: 'label-primary',
                      RequestStatus.FINISHED: 'label-success', RequestStatus.CANCELED: 'label-warning',
                      RequestStatus.ERROR: 'label-danger', RequestStatus.TIMEWALL: 'label-warning'}
        return label_dict[self] if self in label_dict else 'label-default'


class PizarraTask:

    def __init__(self, user_request):
        self.user_request = user_request
        self.output = ''
        self.binary_file_location = ''
        self.return_code = 0
        self.run_time = 0.0

    def process_request(self):
        """
        process the task request
        """
        if not self.contains_malicious_content() and self.compile():
            try:
                self.execute()
            except subprocess.TimeoutExpired:
                self.run_time = self.user_request.max_execution_time
                self.change_status(RequestStatus.TIMEWALL)
        else:
            self.change_status(RequestStatus.ERROR)

        return True

    def contains_malicious_content(self):
        """
        verifies code for malicious content (taken from Tablón)
        """
        # update status
        self.change_status(RequestStatus.VERIFYING)

        # open file and check for forbidden code
        with current_app.open_resource(self.user_request.file_location, mode='r') as f:
            file_content = remove_comments(f.read())
            for i, line in enumerate(file_content.split('\n')):
                # check if line contains any forbidden code
                if any(re.search(fc, line) for fc in current_app.config['FORBIDDEN_CODE']):
                    self.output = 'Found forbidden code at line {}\n\n{}'.format(i + 1, line)
                    return True

        return False

    def compile(self):
        """
        compiles the source and returns if it was successful
        """
        self.change_status(RequestStatus.COMPILING)
        file_location = os.path.join(os.getcwd(), 'app', self.user_request.file_location)
        self.binary_file_location = os.path.splitext(file_location)[0]

        # localhost compile -> gcc-9 -fopenmp omp_hello.c -o hello
        return_code, elapsed_time = self.run_process(
            ['gcc-9', '-fopenmp', file_location, '-o', self.binary_file_location], False)

        return return_code == 0

    def execute(self):
        """
        runs compiled binary
        """
        self.change_status(RequestStatus.RUNNING)
        # TODO run process with inputs and expected outputs
        self.run_process([self.binary_file_location])
        self.change_status(RequestStatus.FINISHED)

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

    def change_status(self, status):
        """
        change status of Request
        """
        self.user_request.status = status
        self.user_request.output = self.output
        self.user_request.run_time = self.run_time

        db.session.add(self.user_request)
        db.session.commit()
