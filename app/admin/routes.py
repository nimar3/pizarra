# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""
import csv
import os

from flask import render_template, request, redirect, url_for, flash, current_app, json
from flask_security.utils import _
from werkzeug.utils import secure_filename

from app import db
from app.admin import blueprint
from app.admin.forms import AssignmentForm, UsersUploadForm
from app.base.models import Assignment, ClassGroup, Request, User, Badge
from app.base.util import random_string, process_date, hash_pass


@blueprint.route('/')
def index():
    return redirect(url_for('.route_admin_home'))


@blueprint.route('/dashboard')
def route_admin_home():
    return render_template('admin_home.html', request_list=Request.query.all())


@blueprint.route('/requests/remove/<id>')
def requests_remove(id):
    user_request = Request.query.filter_by(id=id).first()
    if user_request is not None:
        request_id = user_request.id
        db.session.delete(user_request)
        db.session.commit()
        flash(_('Request with ID #{} removed successfully').format(request_id), 'success')

    return redirect(url_for('.route_admin_home'))


@blueprint.route('/classgroups')
def classgroups():
    return render_template('admin_classgroups.html', classgroup_list=ClassGroup.query.all())


@blueprint.route('/classgroups/remove/<id>')
def classgroups_remove(id):
    classgroup = ClassGroup.query.filter_by(id=id).first()
    if classgroup is not None:
        classgroup_name, classgroup_description = classgroup.name, classgroup.description
        db.session.delete(classgroup)
        db.session.commit()
        flash(_('Group {} ({}) removed successfully').format(classgroup_name, classgroup_description), 'success')

    return redirect(url_for('.classgroups'))


@blueprint.route('/students', methods=['GET', 'POST'])
def students():
    form = UsersUploadForm()
    # if the request is for creating users we validate and then import
    import_result = import_users(form) if request.method == 'POST' and form.validate_on_submit() else None
    student_list = User.query.filter(User.roles.any(name='users')).all()
    return render_template('admin_students.html', student_list=student_list, form=form, import_result=import_result)


@blueprint.route('/students/remove/')
@blueprint.route('/students/remove/<id>')
def students_remove(id):
    user = User.query.filter_by(id=id).first()
    if user is not None and not user.is_admin:
        name, email = user.name, user.email
        db.session.delete(user)
        db.session.commit()
        flash(_('Student {} ({}) was removed successfully').format(name, email), 'success')

    return redirect(url_for('.students'))


@blueprint.route('/students/password/')
@blueprint.route('/students/password/<id>')
def students_password(id):
    user = User.query.filter_by(id=id).first()
    if user is not None:
        random_password = random_string(5)
        user.password = hash_pass(random_password)
        db.session.add(user)
        db.session.commit()
        flash(_('Password for user {} ({}) was reset to <b>{}</b>'.format(user.name, user.email, random_password)),
              'success')

    return redirect(url_for('.students'))


@blueprint.route('/assignments')
def assignments():
    return render_template('admin_assignments.html', assignment_list=Assignment.query.all())


@blueprint.route('/badges')
def badges():
    return render_template('admin_badges.html', badges_list=Badge.query.all())


@blueprint.route('/settings')
def settings():
    return render_template('admin_settings.html')


@blueprint.route('/badges/remove/<id>', methods=['GET', 'POST'])
def badges_remove(id):
    badge = Badge.query.filter_by(name=id).first()
    if badge is not None:
        assignment_name = badge.name
        db.session.delete(badge)
        db.session.commit()
        flash(_('Badge {} removed successfully').format(assignment_name), 'success')

    return redirect(url_for('.assignments'))


@blueprint.route('/assignments/remove/<name>', methods=['GET', 'POST'])
def assignments_remove(name):
    assignment = Assignment.query.filter_by(name=name).first()
    if assignment is not None:
        assignment_name = assignment.name
        db.session.delete(assignment)
        db.session.commit()
        flash(_('Assignment {} removed successfully').format(assignment_name), 'success')

    return redirect(url_for('.assignments'))


@blueprint.route('/assignments/edit/<name>', methods=['GET', 'POST'])
def assignments_edit(name):
    assignment = Assignment.query.filter_by(name=name).first()
    # check if assignment exist
    if assignment is None:
        return redirect(url_for('.assignments'))

    # if assignment was updated
    if 'submit' in request.form:
        form = AssignmentForm(request.form)
        if form.validate_on_submit():
            populate_assignment(assignment, form.data)
            db.session.add(assignment)
            db.session.commit()
            flash(_('Assignment has been updated!'), 'success')
            # returning redirect since name could have been changed
            return redirect(url_for('.assignments_edit', name=assignment.name))

    form = AssignmentForm(request.form, obj=assignment)
    # set default select values for QuerySelectMultipleFields
    # TODO find a default way to avoid this
    form.classgroups.data = assignment.classgroups
    form.badges.data = assignment.badges
    # populate attachments
    attachments = assignment.attachments

    return render_template('admin_assignment_new_edit.html', form=form, edit=True, attachments=attachments)


@blueprint.route('/assignments/new', methods=['GET', 'POST'])
def assignments_new():
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

    return render_template('admin_assignment_new_edit.html', form=form, edit=False)


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
            # check if email exist
            user = User.query.filter_by(email=student['email']).first()
            if user is not None:
                result['error'].append({
                    'email': student['email'],
                    'message': _('email already exist in DB for username {}').format(user.username)
                })
            else:
                student['classgroup'] = form.data['classgroup']
                # create a random password for the user
                student_password = random_string(5)
                student['password'] = student_password
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


def populate_assignment(assignment, data):
    assignment.name = data['name']
    assignment.title = data['title']
    assignment.description = data['description']
    assignment.start_date = process_date(data['start_date'])
    assignment.due_date = process_date(data['due_date'])
    assignment.expected_result = data['expected_result']
    assignment.show_output = data['show_output']
    assignment.points = data['points']
    assignment.classgroups = data['classgroups']
    assignment.badges = data['badges']
