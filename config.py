# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

import os
from os import environ


class Config(object):
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    SECRET_KEY = environ.get('SECRET_KEY', 'pUdos1KbNyLYUvb4P7MvHWmuWSGH0AuYbryi045al9upVyFbyUBys5Xq5s3y')

    # This will create a file in <app> FOLDER
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')

    # For 'in memory' database, please use:
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # THEME SUPPORT
    #  if set then url_for('static', filename='', theme='')
    #  will add the theme name to the static URL:
    #    /static/<DEFAULT_THEME>/filename
    # DEFAULT_THEME = "themes/dark"
    DEFAULT_THEME = None

    # Sample Data
    IMPORT_SAMPLE_DATA = environ.get('IMPORT_SAMPLE_DATA', False)

    # Translations
    SUPPORTED_LANGUAGES = {'es': 'Spanish', 'en': 'English'}
    BABEL_DEFAULT_LOCALE = environ.get('BABEL_DEFAULT_LOCALE', 'en')
    BABEL_DEFAULT_TIMEZONE = environ.get('BABEL_DEFAULT_TIMEZONE', 'UTC')

    # Uploaded files
    UPLOAD_FOLDER = 'uploads'
    FILE_ALLOWED_EXTENSIONS = {'c', 'cpp'}
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1 megabyte

    TIME_BETWEEN_REQUESTS = environ.get('TIME_BETWEEN_REQUESTS', 5)  # in seconds

    # Teams
    TEAM_MAX_SIZE = environ.get('TEAM_MAX_SIZE', 3)

    # Registration
    REGISTRATION_ENABLED = environ.get('REGISTRATION_ENABLED', True)

    # Tasks
    TIMEWALL = environ.get('TIMEWALL', 15.0)  # in seconds
    TIMEWALL_PENALTY = environ.get('TIMEWALL_PENALTY', -10)  # in points
    FORBIDDEN_CODE = ['##', 'fork', 'exec', 'popen', 'fopen', 'open', 'setjmp', 'remove', 'rename', 'system', 'getenv',
                      'MPI_File_open', 'sys/syscall.h', 'sys/stat.h', 'fstream'
                      ]

    # rq
    RQ_DASHBOARD_REDIS_URL = environ.get('RQ_DASHBOARD_REDIS_URL', 'redis://localhost:6379/0')
    QUEUES = ['default', 'kahan']

    # host to connect and execute commands
    REMOTE_HOST = environ.get('REMOTE_HOST', 'kahan.dsic.upv.es')
    REMOTE_USER = environ.get('REMOTE_USER', 'nimar3')
    REMOTE_PATH = environ.get('REMOTE_PATH', '/labos/alumnos/nimar3/pizarra')
    SSH_FILE_PATH = environ.get('SSH_FILE_PATH', os.path.join(BASE_DIR, 'data/keys/id_rsa'))

    # output of JSON responses
    JSONIFY_PRETTYPRINT_REGULAR = True

    # App Mode, TODO change to cli command
    APP_MODE = environ.get('APP_MODE', 'Pizarra')
    COMPILER = environ.get('COMPILER', 'gcc')


class ProductionConfig(Config):
    DEBUG = False

    # Security
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600

    # PostgreSQL database
    SQLALCHEMY_DATABASE_URI = 'postgresql://{}:{}@{}:{}/{}'.format(
        environ.get('DATABASE_USER', 'pizarra'),
        environ.get('DATABASE_PASSWORD', 'pizarra'),
        environ.get('DATABASE_HOST', 'postgres'),
        environ.get('DATABASE_PORT', 5432),
        environ.get('DATABASE_NAME', 'pizarra')
    )


class DebugConfig(Config):
    DEBUG = True


config_dict = {
    'Production': ProductionConfig,
    'Debug': DebugConfig
}
