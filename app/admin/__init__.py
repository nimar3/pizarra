# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2020 - present nimar3
"""

from flask import Blueprint

from app.base.util import verify_is_admin

blueprint = Blueprint(
    'admin_blueprint',
    __name__,
    url_prefix='/admin',
    template_folder='templates',
    static_folder='static'
)

blueprint.before_request(verify_is_admin)
