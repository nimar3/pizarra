# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2020 - nimar3
"""
import yaml

from app.base.models import User


def create_sample(app, db):
    with app.app_context():
        if app.debug:
            for data in yaml.load_all(open('data/users.yml'), Loader=yaml.FullLoader):
                user = User(**data)
                db.session.add(user)
            db.session.commit()
