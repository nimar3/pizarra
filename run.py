# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""
from os import environ
from sys import exit

from app import create_app_worker, create_app_web
from config import config_dict

get_config_mode = environ.get('CONFIG_MODE', 'Debug')
config_mode = []
try:
    config_mode = config_dict[get_config_mode.capitalize()]
except KeyError:
    exit('Error: Invalid CONFIG_MODE environment variable entry.')

app = create_app_web(config_mode) if environ.get('APP_MODE', 'Pizarra') == 'Pizarra' else create_app_worker(config_mode)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
