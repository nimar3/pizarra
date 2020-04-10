# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2020 - Pizarra
"""
from flask_security.forms import Length
from flask_wtf import FlaskForm
from wtforms import PasswordField
from wtforms.validators import InputRequired, EqualTo


class ChangePassword(FlaskForm):
    password = PasswordField('New Password', [InputRequired(), EqualTo('confirm', message='Passwords must match'),
                                              Length(min=4, message='Your password is too short')])
    confirm = PasswordField('Repeat Password')
