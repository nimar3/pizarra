# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""
from flask import render_template

from app.account import blueprint


@blueprint.route('/')
def route_account_home():
    return render_template('account_home.html')


@blueprint.route('/requests')
def route_account_requests():
    return render_template('requests.html')


@blueprint.route('/classgroup')
def route_account_classgroup():
    return render_template('account_classgroup.html')
