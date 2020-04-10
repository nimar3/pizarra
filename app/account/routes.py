# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2020 - Pizarra
"""
from flask import render_template, request, flash
from flask_login import current_user

from app import db
from app.account import blueprint
from app.account.forms import ChangePassword
from app.base.util import random_access_key


@blueprint.route('/')
def route_account_home():
    return render_template('account_profile.html', anchor=None, form=ChangePassword())


@blueprint.route('/requests')
def route_account_requests():
    return render_template('requests.html')


@blueprint.route('/classgroup')
def route_account_classgroup():
    return render_template('account_classgroup.html')


@blueprint.route('/regenerate-key')
def regenerate_key():
    user = current_user
    user.access_key = random_access_key()
    db.session.add(user)
    db.session.commit()
    flash('New Access key has been generated!', 'success')

    return render_template('account_profile.html', anchor="access-key", form=ChangePassword())


@blueprint.route('/update-password', methods=['POST'])
def update_password():
    form = ChangePassword(request.form)

    if form.validate():
        user = current_user
        user.password = form.password.data
        db.session.add(user)
        db.session.commit()
        flash('Password has been updated!', 'success')

    return render_template('account_profile.html', anchor="password", form=form)
