#  -*- encoding: utf-8 -*-
#  """
#  License: MIT
#  Copyright (c) 2020 - Pizarra
#  """
# taken from https://github.com/hackersandslackers/paramiko-tutorial

import logging

from flask import current_app
from paramiko import SSHClient, AutoAddPolicy, RSAKey
from paramiko.auth_handler import AuthenticationException, SSHException
from scp import SCPClient, SCPException


class Singleton:

    def __init__(self, cls):
        self._cls = cls

    def Instance(self):
        try:
            return self._instance
        except AttributeError:
            self._instance = self._cls()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `Instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._cls)


@Singleton
class RemoteClient(object):
    """Client to interact with a remote host via SSH & SCP."""

    def __init__(self):
        self.host = current_app.config['REMOTE_HOST']
        self.user = current_app.config['REMOTE_USER']
        self.ssh_key_filepath = current_app.config['SSH_FILE_PATH']
        self.remote_path = None
        self.client = None
        self.scp = None
        self.conn = None

    def __get_ssh_key(self):
        """
        Fetch locally stored SSH key.
        """
        try:
            self.ssh_key = RSAKey.from_private_key_file(self.ssh_key_filepath)
            logging.info(f'Found SSH key at self {self.ssh_key_filepath}')
        except SSHException as error:
            logging.error(error)
        return self.ssh_key

    def __connect(self):
        """
        Open connection to remote host.
        """
        try:
            self.client = SSHClient()
            self.client.load_system_host_keys()
            self.client.set_missing_host_key_policy(AutoAddPolicy())
            self.client.connect(self.host,
                                username=self.user,
                                pkey=self.__get_ssh_key(),
                                look_for_keys=False,
                                timeout=5000)
            self.scp = SCPClient(self.client.get_transport())
        except AuthenticationException as error:
            logging.info('Authentication failed: did you remember to create an SSH key?')
            logging.error(error)
            raise error
        finally:
            return self.client

    def disconnect(self):
        """
        Close ssh connection.
        """
        self.client.close()
        self.scp.close()

    def bulk_upload(self, files, request_path):
        """
        Upload multiple files to a remote directory.

        :param files: List of strings representing file paths to local files.
        :param request_path: folder where files should be uploaded with the id of the request
        """
        self.remote_path = request_path
        if self.client is None:
            self.client = self.__connect()
        uploads = [self.__upload_single_file(file) for file in files]
        logging.info(f'Finished uploading {len(uploads)} files to {self.remote_path} on {self.host}')

    def __upload_single_file(self, file):
        """Upload a single file to a remote directory."""
        try:
            self.scp.put(file,
                         recursive=True,
                         remote_path=self.remote_path)
        except SCPException as error:
            logging.error(error)
            raise error
        finally:
            logging.info(f'Uploaded {file} to {self.remote_path}')

    def download_file(self, file):
        """Download file from remote host."""
        if self.conn is None:
            self.conn = self.__connect()
        self.scp.get(file)

    def execute_commands(self, commands) -> list:
        """
        Execute multiple commands in succession.

        :param commands: List of unix commands as strings.
        """
        if self.client is None:
            self.client = self.__connect()
        output = []
        for cmd in commands:
            stdin, stdout, stderr = self.client.exec_command(cmd)
            stdout.channel.recv_exit_status()
            response = stdout.readlines()
            for line in response:
                line = line.replace('\n', '')
                output.append(line)
                logging.info(line)

        return output
