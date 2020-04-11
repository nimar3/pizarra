# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2020 - nimar3
"""
from os import environ

import sqla_yaml_fixtures
from sqlalchemy.ext.declarative import declarative_base

BaseModel = declarative_base()


def init_app(app, db=None, directory=None):
    with app.app_context():
        if environ.get('IMPORT_SAMPLE_DATA', True):
            sqla_yaml_fixtures.load(db.Model, db.session, open(directory + '/sample.yml'))


class Sample(object):
    def __init__(self, app=None, db=None, directory='data'):
        self.db = db
        self.directory = str(directory)
        if app is not None and db is not None:
            init_app(app, db, directory)
