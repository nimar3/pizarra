# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""
import os
from datetime import datetime

import lizard
from flask import render_template, redirect, url_for, request, json, current_app, abort
from flask_login import current_user
from flask_security.utils import _
from jinja2 import TemplateNotFound
from werkzeug.utils import secure_filename

from app import db
from app.base.models import Assignment, User, Request
from app.base.util import random_string
from app.home import blueprint
from app.tasks.models import RequestStatus


@blueprint.route('/home')
def home():
    if current_user.is_admin:
        return redirect(url_for('admin_blueprint.route_admin_home'))
    return render_template('home.html')


@blueprint.route('/faq')
def faq():
    return render_template('faq.html')


@blueprint.route('/leaderboard')
def leaderboard():
    return render_template('leaderboard.html')


@blueprint.route('/requests', defaults={'id': None})
@blueprint.route('/requests/<id>')
def requests(id):
    if id is None:
        return render_template('request_list.html')
    user_request = Request.query.filter_by(id=id).first()

    if user_request is None:
        return redirect(url_for('home_blueprint.requests', id=None))

    if user_request.user != current_user and not current_user.is_admin:
        return abort(403)

    contents = None
    if user_request.file_location is not None:
        with current_app.open_resource(user_request.file_location, mode='r') as f:
            contents = f.read()

    # prettify the JSON and remove the filename location for security
    code_analysis = user_request.code_analysis
    if code_analysis is not None:
        del code_analysis['filename']
        code_analysis = json.dumps(code_analysis, sort_keys=True, indent=2)

    return render_template('request.html', user_request=user_request, contents=contents, code_analysis=code_analysis)


@blueprint.route('/assignments/', defaults={'name': None}, methods=['GET'])
@blueprint.route('/assignments/<name>', methods=['GET'])
def assignments(name):
    # list of assignments
    if name is None:
        return render_template('assignment_list.html', assignments=get_assignments_ordered())

    # search for assignment
    assignment = Assignment.query.filter_by(name=name).first()
    if assignment is None:
        return redirect(url_for('.assignments'))

    # only students with the assignment or admins can see
    if not current_user.has_role('admins') and assignment not in current_user.classgroup.assignments:
        return render_template('page-404.html'), 404

    # build url to submit assignment
    protocol, path = request.base_url.split('//')
    submit_url = protocol + '//' + current_user.username + ':' + current_user.access_token + '@' + path

    # assignment full description
    return render_template('assignment.html', assignment=assignment, submit_url=submit_url)


@blueprint.route('/assignments/<name>', methods=['POST'])
def send_assignment(name):
    # auth the user
    username, access_token = request.authorization['username'], request.authorization['password']
    user = User.query.filter_by(username=username, access_token=access_token).first()
    if user is None:
        return build_response(_('Authentication failed'), 400)

    # search the assignment
    assignment = Assignment.query.filter_by(name=name).first()
    if assignment is None:
        return build_response(_('Unable to find Assignment'), 400)

    # check if user is able to queue a request
    if not user.is_admin:
        if not assignment.started:
            return build_response(_('Assignment has not started yet'), 400)
        if assignment.expired:
            return build_response(_('Assignment is closed and not accepting any more requests'), 400)
        if user.quota <= 0:
            return build_response(
                _('You have used all your Quota for sending Requests. Please contact an administrator'), 400)

    # check if file was sent with request
    if 'file' not in request.files:
        return build_response(_('There is no file in this Request'), 400)

    # TODO check file size, file extension and other security issues

    file = request.files['file']
    filename = '-'.join(
        [datetime.today().strftime('%Y-%m-%d'), user.username, random_string(10), secure_filename(file.filename)])
    file_location_relative = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file_location = os.path.join('app', file_location_relative)
    file.save(file_location)

    # create the request
    user_request = Request()
    user_request.assignment = assignment
    user_request.user = user
    user_request.file_location = file_location_relative
    user_request.status = RequestStatus.CREATED

    # analyze code with lizard
    code_analysis = lizard.analyze_file(file_location)
    user_request.code_analysis = code_analysis.function_list[0].__dict__

    db.session.add(user_request)
    db.session.commit()

    request_url = request.host_url[:-1] + url_for('.requests', id=user_request.id)

    return build_response(_('Request created, please navigate to {} to check the results'.format(request_url)), 201)


@blueprint.route('/<template>')
def route_template(template):
    try:
        return render_template(template + '.html')

    except TemplateNotFound:
        return render_template('page-404.html'), 404

    except:
        return render_template('page-500.html'), 500


def get_assignments_ordered():
    """
    returns the list of all available Assignments for the user ordered first with the opened Assignments and
    after that the closed Assignments
    """
    user_assignments = Assignment.query.all() if current_user.is_admin else current_user.classgroup.assignments
    open_assignments = [x for x in user_assignments if not x.expired]
    closed_assignments = [x for x in user_assignments if x.expired]
    return open_assignments + closed_assignments


def build_response(message, status_code):
    """
    returns a response in JSON format with the message and status code provided
    """
    response = current_app.response_class(
        response=json.dumps({
            'code': status_code,
            'message': message
        }, indent=2),
        status=status_code,
        mimetype='application/json'
    )
    return response
