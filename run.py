# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""
from os import environ
from sys import exit

from flask import session, request, current_app
from flask_babel import Babel
from flask_migrate import Migrate

from app import create_app, db
from config import config_dict
from data import Sample

get_config_mode = environ.get('CONFIG_MODE', 'Debug')
config_mode = []
try:
    config_mode = config_dict[get_config_mode.capitalize()]
except KeyError:
    exit('Error: Invalid CONFIG_MODE environment variable entry.')

app = create_app(config_mode)
Migrate(app, db)
Sample(app, db)
babel = Babel(app)


@babel.localeselector
def get_locale():
    # if the user has set up the language manually it will be stored in the session,
    # so we use the locale from the user settings
    # TODO see why this works here but not in base/routes.py
    try:
        language = session['language']
    except KeyError:
        language = None
    if language is not None:
        return language
    return request.accept_languages.best_match(current_app.config['SUPPORTED_LANGUAGES'].keys())


if __name__ == "__main__":
    app.run(debug=True)
