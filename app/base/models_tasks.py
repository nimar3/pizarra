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
        self.return_code = 0

    def process_request(self):
        """
        process the task request
        """
        if not self.contains_malicious_content():
            compiled_binary = self.compile()
            if self.return_code == 0:
                # only execute if it was compiled successfully
                try:
                    elapsed_time = self.execute(compiled_binary)
                    self.change_status(RequestStatus.FINISHED, elapsed_time)
                except subprocess.TimeoutExpired:
                    self.change_status(RequestStatus.TIMEWALL, current_app.config['TIMEWALL'])
            else:
                self.change_status(RequestStatus.ERROR)

        return True

    def contains_malicious_content(self):
        """
        verifies code for malicious content, taken from Tablón
        updates output if found
        """

        # update status
        self.change_status(RequestStatus.VERIFYING)

        # open file and check for forbidden code
        with current_app.open_resource(self.user_request.file_location, mode='r') as f:
            file_content = remove_comments(f.read())
            forbidden_code_list = current_app.config['FORBIDDEN_CODE']
            for i, line in enumerate(file_content.split('\n')):
                # check if line contains any forbidden code
                if any(re.search(fc, line) for fc in forbidden_code_list):
                    self.output = 'Found forbidden code at line {}\n\n{}'.format(i + 1, line)
                    self.change_status(RequestStatus.ERROR)
                    return True

        return False

    def compile(self):
        """
        compiles the source and return the binary to execute
        """
        self.change_status(RequestStatus.COMPILING)
        file_location = os.path.join(os.getcwd(), 'app', self.user_request.file_location)
        file_binary_location = os.path.splitext(file_location)[0]

        # localhost compile -> gcc-9 -fopenmp omp_hello.c -o hello
        self.run_process(['gcc-9', '-fopenmp', file_location, '-o', file_binary_location])

        return file_binary_location

    def execute(self, binary_file):
        """
        runs compiled binary
        """
        self.change_status(RequestStatus.RUNNING)
        return self.run_process([binary_file])

    def change_status(self, status, elapsed_time=0.0):
        """
        change status of Request
        """
        self.user_request.status = status
        self.user_request.output = self.output
        self.user_request.run_time = elapsed_time
        db.session.add(self.user_request)
        db.session.commit()

    def run_process(self, args: list):
        """
        runs a subprocess and updates the return code and output, returns execution time
        """
        start = time.time()
        output = subprocess.run(args, stdout=subprocess.PIPE, universal_newlines=True,
                                timeout=current_app.config['TIMEWALL'])
        elapsed_time = time.time() - start
        try:
            output.check_returncode()
            self.output = output.stdout
        except subprocess.CalledProcessError:
            # TODO check how to capture errors
            self.output = output.stderr
        self.return_code = output.returncode

        return elapsed_time
