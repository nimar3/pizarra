# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""
from flask import render_template

from app.admin import blueprint
from app.base.models import ClassGroup


@blueprint.route('/')
def route_admin_home():
    return render_template('admin_home.html')


@blueprint.route('/assignment/new')
def route_assignment_new():
    classgroups = ClassGroup.query.all()
    return render_template('assignment_new.html', classgroups=classgroups)
