# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2020 - nimar3
"""

import sqla_yaml_fixtures
from flask import current_app


class Sample(object):

    def init_app(self, app, db):
        self.app = app
        self.db = db

    def import_sample_data(self):
        with self.app.app_context():
            if current_app.config['IMPORT_SAMPLE_DATA']:
                sqla_yaml_fixtures.load(self.db.Model, self.db.session, open('data/sample.yml'))

    def __init__(self, app=None, db=None, directory='data'):
        self.app = None
        self.db = None
