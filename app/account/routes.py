# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""
from flask import render_template
from flask_login import current_user

from app.account import blueprint
from app.base.models import Request


@blueprint.route('/')
def route_account_home():
    return  render_template('home.html')

@blueprint.route('/requests')
def route_account_requests():
    requests = Request.query.filter_by(user_id=current_user.id).order_by(Request.timestamp.desc())
    return render_template('requests.html', requests=requests)
