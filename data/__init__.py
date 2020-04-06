# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2020 - nimar3
"""
from os import environ

import yaml

from app.base.models import User, Role, ClassGroup, Team


class Sample(object):
    def __init__(self, app=None, db=None, directory='data'):
        self.db = db
        self.directory = str(directory)
        if app is not None and db is not None:
            self.init_app(app, db, directory)

    def init_app(self, app, db=None, directory=None):
        with app.app_context():
            if environ.get('IMPORT_SAMPLE_DATA', True):
                data = yaml.load(open(directory + '/sample.yml'), Loader=yaml.FullLoader)
                for user in data['users']:
                    db.session.add(User(**user))
                for role in data['roles']:
                    db.session.add(Role(**role))
                for classgroup in data['classgroups']:
                    db.session.add(ClassGroup(**classgroup))
                for team in data['teams']:
                    db.session.add(Team(**team))
                db.session.commit()
