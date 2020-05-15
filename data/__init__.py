#  -*- encoding: utf-8 -*-
#  """
#  License: MIT
#  Copyright (c) 2020 - Pizarra
#  """

import sqla_yaml_fixtures


class Sample(object):

    def init_app(self, app, db):
        self.app = app
        self.db = db

    def import_sample_data(self):
        with self.app.app_context():
            if self.app.config['IMPORT_SAMPLE_DATA']:
                sqla_yaml_fixtures.load(self.db.Model, self.db.session, open('data/sample.yml'))

    def __init__(self):
        self.app = None
        self.db = None
