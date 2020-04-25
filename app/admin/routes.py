# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""
import csv
import os
from datetime import datetime

from flask import render_template, request, redirect, url_for, flash, current_app, json
from flask_security.utils import _
from werkzeug.utils import secure_filename

from app import db
from app.admin import blueprint
from app.admin.forms import AssignmentForm, UsersUploadForm
from app.base.models import Assignment, ClassGroup, Badge, Request, User, Role
from app.base.util import random_string


@blueprint.route('/')
def index():
    return redirect(url_for('.route_admin_home'))


@blueprint.route('/dashboard')
def route_admin_home():
    return render_template('admin_home.html', request_list=Request.query.all())


@blueprint.route('/classgroups')
def classgroups():
    return render_template('admin_classgroups.html', classgroup_list=ClassGroup.query.all())


@blueprint.route('/students', methods=['GET', 'POST'])
def students():
    form = UsersUploadForm()
    # if the request is for creating users we validate and then import
    import_result = import_users(form) if request.method == 'POST' and form.validate_on_submit() else None
    student_list = User.query.filter(User.roles.any(name='users')).all()
    return render_template('admin_students.html', student_list=student_list, form=form, import_result=import_result)


@blueprint.route('/assignments')
def assignments():
    return render_template('admin_assignments.html', assignment_list=Assignment.query.all())


@blueprint.route('/settings')
def settings():
    return render_template('admin_settings.html')


@blueprint.route('/assignment/new', methods=['GET', 'POST'])
def route_assignment_new():
    form = AssignmentForm(request.form)
    if 'submit' in request.form:
        # read form data
        name = form.data['name']

        # Locate assignment
        assignment = Assignment.query.filter_by(name=name).first()

        if assignment is None:
            assignment = Assignment(**form.data)

        db.session.add(assignment)
        db.session.commit()
        flash(_('New Assignment has been created!'), 'success')

        return redirect(url_for('home_blueprint.assignments', name=assignment.name))

    return render_template('assignment_new.html', form=form)


def import_users(form):
    result = {'success': [], 'error': []}
    f = form.file.data
    # TODO avoid storing file
    # create file
    filename = secure_filename(f.filename)
    file_location = os.path.join('app', current_app.config['UPLOAD_FOLDER'], filename)
    f.save(file_location)
    # open file
    with open(file_location, newline='') as csvfile:
        # create a list with dicts for each user
        csv_dicts = [{k: v for k, v in row.items()} for row in csv.DictReader(csvfile, skipinitialspace=True)]
        for student in csv_dicts:
            # create a random password for the user
            student_password = random_string(5)
            student['password'] = student_password
            student['classgroup'] = form.data['classgroup']
            # TODO check if user and email exist
            # create and store User
            student = User(**student)
            db.session.add(student)
            db.session.commit()
            # store result
            result['success'].append(
                {'email': student.email, 'username': student.username, 'password': student_password})

    if len(result['error']) > 0:
        flash('Imported file with errors', 'error')
    else:
        flash('File imported successfully', 'success')
    return json.dumps(result, indent=2)



