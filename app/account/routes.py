# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2020 - Pizarra
"""
from flask import render_template, request, flash, redirect, url_for, current_app
from flask_login import current_user
from flask_security.utils import _

from app import db
from app.account import blueprint
from app.account.forms import ChangePassword, CreateTeam
from app.base.models import UserBadge, Badge, Team
from app.base.util import random_string, hash_pass


@blueprint.route('/', defaults={'anchor': 'activity'})
@blueprint.route('/<anchor>')
def route_account_home(anchor):
    anchors = ['activity', 'badges', 'classgroup', 'password', 'access-key']
    if anchor is not None and anchor not in anchors:
        return redirect(url_for('account_blueprint.route_account_home', anchor=None))

    return render_template('profile.html', anchor=anchor, activity_stream=activity_stream(), form=ChangePassword(),
                           form_team=CreateTeam())


@blueprint.route('/regenerate-key')
def route_regenerate_key():
    user = current_user
    user.access_token = random_string()
    db.session.add(user)
    db.session.commit()
    flash(_('New Access key has been generated!'), 'success')

    return redirect(url_for('account_blueprint.route_account_home', anchor='access-key'))


@blueprint.route('/team/join/<key>')
def join_team(key):
    if key is not None:
        # try to find team with key
        team = Team.query.filter_by(key=key).first()
        if team is not None:
            if team != current_user.team:
                # check if team is not full
                if len(team.members) < current_app.config['TEAM_MAX_SIZE']:
                    # set new team to user
                    user_old_team = current_user.team
                    current_user.team = team
                    db.session.add(current_user)
                    db.session.commit()
                    check_for_empty_team(user_old_team)
                    flash(_('You joined Team {}').format(team.name), 'success')
                else:
                    flash(_('You are unable to join team {} because is full').format(team.name), 'error')
            else:
                flash(_('You already belong to team {}').format(team.name), 'error')
        else:
            flash(_('Team with key {} was not found').format(key), 'error')

    return redirect(url_for('account_blueprint.route_account_home', anchor='activity'))


@blueprint.route('/team/leave')
def leave_team():
    if current_user.team is not None:
        user_old_team = current_user.team
        current_user.team = None
        db.session.add(current_user)
        db.session.commit()
        check_for_empty_team(user_old_team)
        flash(_('You left the team successfully'), 'success')

    return redirect(url_for('account_blueprint.route_account_home', anchor='activity'))


@blueprint.route('/team/create', methods=['POST'])
def create_team():
    if current_user.team is not None:
        flash(_('You cannot create a new Team until you leave your current one'), 'error')
    else:
        team_name = request.form['name']
        team = Team.query.filter_by(name=team_name).first()
        if team is not None:
            flash(_('Team with name {} already exist, please pick another one').format(team.name), 'error')
        else:
            team = Team()
            team.name = team_name
            db.session.add(team)
            db.session.commit()
            current_user.team = team
            db.session.add(current_user)
            db.session.commit()
            flash(_('You created and joined the team {}').format(team.name), 'success')

    return redirect(url_for('account_blueprint.route_account_home', anchor='activity'))


@blueprint.route('/update-password', methods=['POST'])
def route_update_password():
    form = ChangePassword(request.form)

    if form.validate():
        user = current_user
        user.password = hash_pass(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_('Password has been updated!'), 'success')
    else:
        flash(_('Unable to update password'), 'error')

    return render_template('profile.html', anchor='password', activity_stream=activity_stream(), form=form,
                           form_team=CreateTeam())


def activity_stream():
    """builds the dict for showing the activity of the user in his profile"""

    # first entrance is the user registered time
    stream = {current_user.registered_at.strftime('%Y-%m-%d'): [
        {'time': current_user.registered_at.strftime('%X'),
         'type': 'registered'}
    ]}

    # TODO move to smaller functions and reuse code
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


def check_for_empty_team(team):
    if team is not None and len(team.members) == 0:
        db.session.delete(team)
        db.session.commit()
