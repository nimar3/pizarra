# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2002 - Pizarra
"""

from importlib import import_module
from logging import basicConfig, DEBUG, getLogger, StreamHandler
from os import path

import redis
import rq_dashboard
from flask import Flask, url_for, session, request, current_app
from flask_babel import Babel
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from rq import Connection, Worker

from data import Sample

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
        basicConfig(filename='error.log', level=DEBUG)
        logger = getLogger()
        logger.addHandler(StreamHandler())
    except:
        pass


def apply_themes(app):
    """
    Add support for themes.

    If DEFAULT_THEME is set then all calls to
      url_for('static', filename='')
      will modfify the url to include the theme name

    The theme parameter can be set directly in url_for as well:
      ex. url_for('static', filename='', theme='')

    If the file cannot be found in the /static/<theme>/ location then
      the url will not be modified and the file is expected to be
      in the default /static/ location
    """

    @app.context_processor
    def override_url_for():
        return dict(url_for=_generate_url_for_theme)

    def _generate_url_for_theme(endpoint, **values):
        if endpoint.endswith('static'):
            themename = values.get('theme', None) or \
                        app.config.get('DEFAULT_THEME', None)
            if themename:
                theme_file = "{}/{}".format(themename, values.get('filename', ''))
                if path.isfile(path.join(app.static_folder, theme_file)):
                    values['filename'] = theme_file
        return url_for(endpoint, **values)


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
    apply_themes(app)
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
    # TODO see why this works here but not in base/routes.py
    try:
        language = session['language']
    except KeyError:
        language = None
    if language is not None:
        return language
    return request.accept_languages.best_match(current_app.config['SUPPORTED_LANGUAGES'].keys())
