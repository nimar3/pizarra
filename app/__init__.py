# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2002 - Pizarra
"""

from importlib import import_module
from logging import basicConfig, DEBUG, getLogger, StreamHandler

import redis
import rq_dashboard
from flask import Flask, session, request, current_app
from flask_babel import Babel
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from rq import Connection, Worker

from app.data import Sample

db = SQLAlchemy()
login_manager = LoginManager()
babel = Babel()
sample = Sample()


def register_rq_dashboard(app):
    app.config.from_object(rq_dashboard.default_settings)
    app.register_blueprint(rq_dashboard.blueprint, url_prefix='/admin/scheduler')


def register_global_variables(app):
    app.jinja_env.globals['STATIC_PZ'] = 'assets/pizarra/img/'


def register_extensions(app):
    db.init_app(app)
    babel.init_app(app)
    login_manager.init_app(app)
    sample.init_app(app, db)


def register_blueprints(app):
    for module_name in ('base', 'home', 'account', 'admin'):
        module = import_module('app.{}.routes'.format(module_name))
        app.register_blueprint(module.blueprint)


def initialize_database(app):
    if app.config['IMPORT_SAMPLE_DATA']:
        with app.app_context():
            db.drop_all()
            db.create_all()


def import_sample_data():
    sample.import_sample_data()


def configure_database(app):
    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()


def configure_logs(app):
    # soft logging
    try:
        basicConfig(filename='error.log', level=app.config['LOG_LEVEL'])
        logger = getLogger()
        logger.addHandler(StreamHandler())
    except:
        pass


def create_app_web(config):
    app = Flask(__name__, static_folder='base/static')
    app.config.from_object(config)

    register_rq_dashboard(app)
    register_global_variables(app)
    register_extensions(app)
    register_blueprints(app)
    initialize_database(app)
    configure_database(app)
    configure_logs(app)
    import_sample_data()

    return app


def create_app_worker(config):
    app = Flask(__name__, static_folder='base/static')
    app.config.from_object(config)
    register_extensions(app)
    configure_database(app)
    configure_logs(app)
    with app.app_context():
        redis_url = app.config["RQ_DASHBOARD_REDIS_URL"]
        redis_connection = redis.from_url(redis_url)
        with Connection(redis_connection):
            worker = Worker(app.config['QUEUES'])
            worker.work(with_scheduler=True)


@babel.localeselector
def get_locale():
    # if the user has set up the language manually it will be stored in the session,
    # so we use the locale from the user settings
    try:
        language = session['language']
    except KeyError:
        language = None
    if language is not None:
        return language
    return request.accept_languages.best_match(current_app.config['SUPPORTED_LANGUAGES'].keys())
