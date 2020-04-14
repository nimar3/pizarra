# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""
from flask import render_template, redirect, url_for
from flask_login import current_user

from app.base.models import Assignment
from app.home import blueprint


@blueprint.route('/home')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('base_blueprint.login'))

    return render_template('home.html')


@blueprint.route('/assignments/', defaults={'name': None})
@blueprint.route('/assignments/<name>')
def route_assignments(name):
    # list of assignments
    if name is None:
        assignments = Assignment.query.all() if current_user.is_admin else current_user.classgroup.assignments
        return render_template('assignment_list.html', assignments=assignments)

    # search for assignment
    assignment = Assignment.query.filter_by(name=name).first()
    if assignment is None:
        return redirect(url_for('home_blueprint.route_assignments'))

    # only students with the assignment or admins can see
    if assignment not in current_user.classgroup.assignments and not current_user.has_role('admin'):
        return render_template('page-404.html'), 404

    # assignment full description
    return render_template('assignment.html', assignment=assignment)
