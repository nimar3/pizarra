# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""
from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound

from app.base.models import Assignment
from app.home import blueprint


@blueprint.route('/index')
@login_required
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('base_blueprint.login'))

    return render_template('index.html')


@blueprint.route('/assignment')
@blueprint.route('/assignment/<id>')
def route_assignment(id):
    assignment = Assignment.query.filter_by(id=id).first()
    return render_template('assignment.html', assignment=assignment)


@blueprint.route('/<template>')
def route_template(template):
    if not current_user.is_authenticated:
        return redirect(url_for('base_blueprint.login'))

    try:

        return render_template(template + '.html')

    except TemplateNotFound:
        return render_template('page-404.html'), 404

    except:
        return render_template('page-500.html'), 500
