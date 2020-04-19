# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""
from datetime import datetime

import redis
from flask import render_template, request, jsonify, current_app, redirect, url_for, flash
from rq import Connection, Queue

from app import db
from app.admin import blueprint
from app.admin.forms import AssignmentForm
from app.base.models import Assignment, ClassGroup, Badge, Request, User
from app.tasks.models import simple_task


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


@blueprint.route('/students')
def students():
    # TODO change to SQL Query
    student_list = [x for x in User.query.all() if not x.is_admin]
    return render_template('admin_students.html', student_list=student_list)


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


@blueprint.route('/create-task')
def create_task():
    with Connection(redis.from_url(current_app.config["REDIS_URL"])):
        q = Queue()
        task = q.enqueue(simple_task)
    response_object = {
        "status": "success",
        "data": {
            "task_id": task.get_id()
        }
    }
    return jsonify(response_object), 202


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


def process_date(string_date):
    """ transforms a string date to datetime """
    if string_date is not None and string_date != '':
        try:
            date = datetime.strptime(string_date, '%Y-%m-%d %H:%M')
            return date
        except ValueError:
            pass

    return None
