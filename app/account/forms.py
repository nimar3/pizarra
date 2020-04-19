# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2020 - Pizarra
"""
from flask_security.forms import Length
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField
from wtforms.validators import InputRequired, EqualTo, DataRequired


class ChangePassword(FlaskForm):
    password = PasswordField('New Password', [InputRequired(), EqualTo('confirm', message='Passwords must match'),
                                              Length(min=4, message='Your password is too short')])
    confirm = PasswordField('Repeat Password')


class CreateTeam(FlaskForm):
    name = StringField('Name', id='name', validators=[DataRequired()])
