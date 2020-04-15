# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2020 - Pizarra
"""
from flask import render_template, request, flash, redirect, url_for
from flask_login import current_user

from app import db
from app.account import blueprint
from app.account.forms import ChangePassword
from app.base.util import random_string, hash_pass


@blueprint.route('/', defaults={'anchor': None})
@blueprint.route('/<anchor>')
def route_account_home(anchor):
    anchors = ['activity', 'badges', 'classgroup', 'password', 'access-key']
    if anchor is not None and anchor not in anchors:
        return redirect(url_for('account_blueprint.route_account_home', anchor=None))

    return render_template('account_profile.html', anchor=anchor, form=ChangePassword())


@blueprint.route('/requests')
def route_account_requests():
    return render_template('requests.html')


@blueprint.route('/regenerate-key')
def route_regenerate_key():
    user = current_user
    user.access_token = random_string()
    db.session.add(user)
    db.session.commit()
    flash('New Access key has been generated!', 'success')

    return redirect(url_for('account_blueprint.route_account_home', anchor='access-key'))


@blueprint.route('/update-password', methods=['POST'])
def route_update_password():
    form = ChangePassword(request.form)

    if form.validate():
        user = current_user
        user.password = hash_pass(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Password has been updated!', 'success')

    return render_template('account_profile.html', anchor="password", form=form)
