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
        compiled_binary = self.compile()
        if self.return_code == 0:
            # only execute if it was compiled successfully
            self.execute(compiled_binary)
            self.change_status(RequestStatus.FINISHED)
        else:
            self.change_status(RequestStatus.ERROR)


        return True

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

    def execute(self, bin):
        """
        runs compiled binary
        """
        self.change_status(RequestStatus.RUNNING)
        self.run_process([bin])

    def change_status(self, status):
        """
        change status of Request
        """
        self.user_request.status = status
        self.user_request.output = '\n'.join(self.output)
        db.session.add(self.user_request)
        db.session.commit()

    def run_process(self, args: list):
        """
        runs a subprocess and updates the return code and output
        """
        process = subprocess.Popen(args, stdout=subprocess.PIPE, universal_newlines=True)

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
