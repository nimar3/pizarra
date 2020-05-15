# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""
from datetime import datetime

from flask import render_template, redirect, request, url_for, session, current_app
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user
)

from app import db, login_manager
from app.base import blueprint
from app.base.forms import LoginForm, CreateAccountForm
from app.base.models import User
from app.base.util import verify_pass


@blueprint.route('/')
def route_default():
    return redirect(url_for('base_blueprint.login'))


# Login & Registration

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    if 'login' in request.form:

        # read form data
        username = request.form['username']
        password = request.form['password']

        # Locate user
        user = User.query.filter_by(username=username).first()

        if user is None:
            user = User.query.filter_by(email=username).first()

        # Check the password
        if user and verify_pass(password, user.password):
            update_user_at_login(user)
            login_user(user)
            return redirect(url_for('base_blueprint.route_default'))

        # Something (user or pass) is not ok
        return render_template('login/login.html', msg='Wrong user or password', form=login_form)

    if not current_user.is_authenticated:
        return render_template('login/login.html',
                               form=login_form)
    return redirect(url_for('home_blueprint.home'))


@blueprint.route('/create_user', methods=['GET', 'POST'])
def create_user():
    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:

        email = request.form['email']

        user = User.query.filter_by(email=email).first()
        if user:
            return render_template('login/register.html', msg='Email already registered', form=create_account_form)

        # else we can create the user
        user = User(**request.form)
        db.session.add(user)
        db.session.commit()

        return render_template('login/register.html', success='User created please <a href="/login">login</a>',
                               form=create_account_form)

    else:
        return render_template('login/register.html', form=create_account_form)


@blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('base_blueprint.login'))


@blueprint.route('/language/<language>')
def set_language(language=None):
    if language is not None and language in current_app.config['SUPPORTED_LANGUAGES']:
        session['language'] = language
    return redirect(request.args.get('path'))


# Errors
@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('errors/page_403.html'), 403


@blueprint.errorhandler(403)
def access_forbidden():
    return render_template('errors/page_403.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('errors/page_404.html'), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('errors/page_500.html'), 500


def update_user_at_login(user):
    user.last_login_ip = request.remote_addr
    user.last_login_at = datetime.utcnow()
    user.login_count += 1
    db.session.commit()
