# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2020 - nimar3
"""

import sqla_yaml_fixtures
from flask import current_app


def init_app(app, db=None, directory=None):
    with app.app_context():
        if current_app.config['IMPORT_SAMPLE_DATA']:
            sqla_yaml_fixtures.load(db.Model, db.session, open(directory + '/sample.yml'))


class Sample(object):
    def __init__(self, app=None, db=None, directory='data'):
        self.db = db
        self.directory = str(directory)
        if app is not None and db is not None:
            init_app(app, db, directory)
