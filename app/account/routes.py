# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2020 - Pizarra
"""
from flask import render_template, request, flash, redirect, url_for
from flask_login import current_user
from flask_security.utils import _

from app import db
from app.account import blueprint
from app.account.forms import ChangePassword
from app.base.models import UserBadge, Badge
from app.base.util import random_string, hash_pass


@blueprint.route('/', defaults={'anchor': 'activity'})
@blueprint.route('/<anchor>')
def route_account_home(anchor):
    anchors = ['activity', 'badges', 'classgroup', 'password', 'access-key']
    if anchor is not None and anchor not in anchors:
        return redirect(url_for('account_blueprint.route_account_home', anchor=None))

    return render_template('profile.html', anchor=anchor, activity_stream=activity_stream(), form=ChangePassword())


@blueprint.route('/regenerate-key')
def route_regenerate_key():
    user = current_user
    user.access_token = random_string()
    db.session.add(user)
    db.session.commit()
    flash(_('New Access key has been generated!'), 'success')

    return redirect(url_for('account_blueprint.route_account_home', anchor='access-key'))


@blueprint.route('/update-password', methods=['POST'])
def route_update_password():
    form = ChangePassword(request.form)

    if form.validate():
        user = current_user
        user.password = hash_pass(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_('Password has been updated!'), 'success')

    return render_template('profile.html', anchor="password", form=form)


def activity_stream():
    """builds the dict for showing the activity of the user in his profile"""

    # first entrance is the user registered time
    stream = {current_user.registered_at.strftime('%Y-%m-%d'): [
        {'time': current_user.registered_at.strftime('%X'),
         'type': 'registered'}
    ]}

    # add all requests
    for user_request in current_user.requests:
        request_date = user_request.timestamp.strftime('%Y-%m-%d')
        item = {'time': user_request.timestamp.strftime('%X'),
                'type': 'request',
                'object': user_request
                }

        if request_date not in stream:
            stream[request_date] = [item]
        else:
            stream[request_date].append(item)

    # add all badges
    user_badges = UserBadge.query.filter_by(user_id=current_user.id).all()
    for user_badge in user_badges:
        item_date = user_badge.timestamp.strftime('%Y-%m-%d')
        item = {'time': user_badge.timestamp.strftime('%X'),
                'type': 'badge',
                'object': Badge.query.filter_by(id=user_badge.badge_id).first()
                }

        if item_date not in stream:
            stream[item_date] = [item]
        else:
            stream[item_date].append(item)

    return stream
