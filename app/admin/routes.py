# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""
import time

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
def login():
    assignment_form = AssignmentForm(request.form)
    assignment_form.classgroups.choices = [(x.id, x.description) for x in ClassGroup.query.all()]
    if 'submit' in request.form:
        # read form data
        name = request.form['name']

        # Locate assignment
        assignment = Assignment.query.filter_by(name=name).first()

        if assignment is None:
            assignment = Assignment(**request.form)

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
