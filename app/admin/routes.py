# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""
from datetime import datetime

import redis
from flask import render_template, request, jsonify, current_app
from rq import Connection, Queue

from app import db
from app.admin import blueprint
from app.admin.forms import AssignmentForm
from app.base.models import Assignment, ClassGroup
from app.tasks.models import simple_task


@blueprint.route('/')
def route_admin_home():
    return render_template('admin_home.html')


@blueprint.route('/assignment/new', methods=['GET', 'POST'])
def route_assignment_new():
    assignment_form = AssignmentForm(request.form)
    assignment_form.classgroups.choices = [(x.id, x.description) for x in ClassGroup.query.all()]
    if 'submit' in request.form:
        # read form data
        name = assignment_form.data['name']

        # Locate assignment
        assignment = Assignment.query.filter_by(name=name).first()

        if assignment is None:
            assignment = create_assignment(assignment_form.data)

        db.session.add(assignment)
        db.session.commit()

        # Something (user or pass) is not ok
        return render_template('assignment_new.html', msg='Wrong user or password', form=assignment_form)

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
    # start and due dates
    date_start_due = [x.strip() for x in data['date'].split('-')]
    assignment.start_date, assignment.due_date = list(
        map(lambda x: datetime.strptime(x, '%Y/%m/%d %H:%M'), date_start_due))
    # each class group must be fetched
    assignment.classgroups = list(map(lambda x: ClassGroup.query.filter_by(id=x).first(), set(data['classgroups'])))
    return assignment
