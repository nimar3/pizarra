# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""
from flask import render_template, request
from wtforms import SelectMultipleField

from app.admin import blueprint
from app.admin.forms import AssignmentForm
from app.base.models import Assignment, ClassGroup


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

        # Locate user
        user = Assignment.query.filter_by(name=name).first()

        # Something (user or pass) is not ok
        return render_template('assignment_new.html', msg='Wrong user or password', form=assignment_form)

    return render_template('assignment_new.html', form=assignment_form)
