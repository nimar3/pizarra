# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""
import csv
import os
from datetime import datetime

from flask import render_template, request, redirect, url_for, flash, current_app, json
from werkzeug.utils import secure_filename

from app import db
from app.admin import blueprint
from app.admin.forms import AssignmentForm, UsersUploadForm
from app.base.models import Assignment, ClassGroup, Badge, Request, User
from app.base.util import random_string


@blueprint.route('/')
def index():
    return redirect(url_for('.route_admin_home'))


@blueprint.route('/dashboard')
def route_admin_home():
    request_list = Request.query.all()
    return render_template('admin_home.html', request_list=request_list)


@blueprint.route('/classgroups')
def classgroups():
    classgroup_list = ClassGroup.query.all()
    return render_template('admin_classgroups.html', classgroup_list=classgroup_list)


@blueprint.route('/students', methods=['GET', 'POST'])
def students():
    import_result = None
    if request.method == 'POST':
        form = UsersUploadForm()
        if form.validate_on_submit():
            import_result = import_users(form)

    # TODO change to SQL Query
    student_list = [x for x in User.query.all() if not x.is_admin]
    form = UsersUploadForm()
    form.classgroup.choices = [(x.id, x.description) for x in ClassGroup.query.all()]
    return render_template('admin_students.html', student_list=student_list, form=form, import_result=import_result)


@blueprint.route('/assignments')
def assignments():
    assignment_list = Assignment.query.all()
    return render_template('admin_assignments.html', assignment_list=assignment_list)


@blueprint.route('/settings')
def settings():
    return render_template('admin_settings.html')


@blueprint.route('/assignment/new', methods=['GET', 'POST'])
def route_assignment_new():
    assignment_form = AssignmentForm(request.form)
    if 'submit' in request.form:
        # read form data
        name = assignment_form.data['name']

        # Locate assignment
        assignment = Assignment.query.filter_by(name=name).first()

        if assignment is None:
            assignment = create_assignment(assignment_form.data)

        db.session.add(assignment)
        db.session.commit()
        flash('New Assignment has been created!', 'success')

        return redirect(url_for('home_blueprint.assignments', name=assignment.name))

    assignment_form.classgroups.choices = [(x.id, x.description) for x in ClassGroup.query.all()]
    assignment_form.badges.choices = [(x.id, x.title + ': ' + x.description) for x in Badge.query.all()]
    return render_template('assignment_new.html', form=assignment_form)


def create_assignment(data):
    assignment = Assignment()
    assignment.name = data['name']
    assignment.title = data['title']
    assignment.description = data['description']
    assignment.start_date = process_date(data['start_date'])
    assignment.due_date = process_date(data['due_date'])
    # each class group must be fetched
    assignment.classgroups = list(map(lambda x: ClassGroup.query.filter_by(id=x).first(), set(data['classgroups'])))
    # each badge must be fetched
    assignment.badges = list(map(lambda x: Badge.query.filter_by(id=x).first(), set(data['badges'])))
    return assignment


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


def process_date(string_date):
    """ transforms a string date to datetime """
    if string_date is not None and string_date != '':
        try:
            date = datetime.strptime(string_date, '%Y-%m-%d %H:%M')
            return date
        except ValueError:
            pass

    return None
