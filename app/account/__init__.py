# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2020 - present nimar3
"""

from flask import Blueprint

from app.base.util import verify_logged_in

blueprint = Blueprint(
    'account_blueprint',
    __name__,
    url_prefix='/my-account',
    template_folder='templates',
    static_folder='static'
)

blueprint.before_request(verify_logged_in)
