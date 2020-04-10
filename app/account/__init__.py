# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2020 - present nimar3
"""

from flask import Blueprint

blueprint = Blueprint(
    'account_blueprint',
    __name__,
    url_prefix='/my-account',
    template_folder='templates',
    static_folder='static'
)
