# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

from flask_migrate import Migrate
from os import environ
from sys import exit

from config import config_dict
from app import create_app, db
from data import Sample

get_config_mode = environ.get('CONFIG_MODE', 'Debug')

try:
    config_mode = config_dict[get_config_mode.capitalize()]
except KeyError:
    exit('Error: Invalid CONFIG_MODE environment variable entry.')

app = create_app(config_mode)
Migrate(app, db)
Sample(app, db)

if __name__ == "__main__":
    app.run()