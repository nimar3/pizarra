# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""
from flask import render_template, redirect, url_for
from flask_login import current_user
from jinja2 import TemplateNotFound

from app.base.models import Assignment
from app.home import blueprint


@blueprint.route('/home')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('base_blueprint.login'))

    return render_template('home.html')


@blueprint.route('/assignments/', defaults={'name': None}, methods=['GET'])
@blueprint.route('/assignments/<name>', methods=['GET'])
def route_assignments(name):
    # list of assignments
    if name is None:
        return render_template('assignment_list.html', assignments=get_assignments_ordered())

    # search for assignment
    assignment = Assignment.query.filter_by(name=name).first()
    if assignment is None:
        return redirect(url_for('home_blueprint.route_assignments'))

    # only students with the assignment or admins can see
    if assignment not in current_user.classgroup.assignments and not current_user.has_role('admin'):
        return render_template('page-404.html'), 404

    # assignment full description
    return render_template('assignment.html', assignment=assignment)


@blueprint.route('/assignments/<name>', methods=['POST'])
def route_send_assignment(name):
    return name


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
    after that the ones the closed Assignments
    """
    assignments = Assignment.query.all() if current_user.is_admin else current_user.classgroup.assignments
    open_assignments = [x for x in assignments if not x.expired]
    closed_assignments = [x for x in assignments if x.expired]
    return open_assignments + closed_assignments
