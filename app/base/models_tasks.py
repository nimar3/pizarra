#  License: MIT
#  Copyright (c) 2020 - Pizarra
#
import enum
import os
import subprocess

from app import db


class RequestStatus(enum.Enum):
    CREATED = 0
    COMPILING = 1
    QUEUED = 2
    DEPLOYING = 3
    WAITING = 4
    RUNNING = 5
    FINISHED = 6
    CANCELED = 7
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
        self.output = []
        self.return_code = 0

    def process_request(self):
        bin = self.compile()
        print(self.output, self.return_code)

        return True

    def compile(self):
        """
        compiles the source and return the binary to execute
        """
        self.change_status(RequestStatus.COMPILING)
        # localhost compile gcc-9 -fopenmp omp_hello.c -o hello
        file_location = os.path.join(os.getcwd(), 'app', self.user_request.file_location)
        file_binary_location = os.path.splitext(file_location)[0]
        process = subprocess.Popen(['gcc-9', '-fopenmp', file_location, '-o', file_binary_location],
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)

        while True:
            line_output = process.stdout.readline()
            if line_output is not None:
                self.output.append(line_output.strip())
            self.return_code = process.poll()
            if self.return_code is not None:
                # Process has finished, read rest of the output
                for line_output in process.stdout.readlines():
                    self.output.append(line_output.strip())
                break

        return file_binary_location

    def execute(self, bin):
        self.change_status(RequestStatus.RUNNING)
        process = subprocess.Popen([bin],
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)

    def change_status(self, status):
        self.user_request.status = status
        db.session.add(self.user_request)
        db.session.commit()

    def run_process(self, args):
        process = subprocess.Popen(args,
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)

        while True:
            line_output = process.stdout.readline()
            if line_output is not None:
                self.output.append(line_output.strip())
            self.return_code = process.poll()
            if self.return_code is not None:
                # Process has finished, read rest of the output
                for line_output in process.stdout.readlines():
                    self.output.append(line_output.strip())
                break
