# -*- encoding: utf-8 -*-
"""
License: MIT
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField
from wtforms.validators import Email, DataRequired


class LoginForm(FlaskForm):
    username = StringField('Username', id='username_login', validators=[DataRequired()])
    password = PasswordField('Password', id='pwd_login', validators=[DataRequired()])


class CreateAccountForm(FlaskForm):
    username = StringField('Username', id='username_create', validators=[DataRequired()])
    email = StringField('Email', id='email_create', validators=[DataRequired(), Email()])
    password = PasswordField('Password', id='pwd_create', validators=[DataRequired()])


class AssignmentForm(FlaskForm):
    name = StringField('Name', id='name', validators=[DataRequired()])
    title = StringField('Title', id='title', validators=[DataRequired()])
    description = StringField('Description', id='description', validators=[DataRequired()])
    header = StringField('Header', id='header', validators=[DataRequired()])
    template = StringField('Template', id='template', validators=[DataRequired()])
    start_date = DateField('StartDate', id='start_date', validators=[DataRequired()])
    due_date = DateField('DueDate', id='due_date', validators=[DataRequired()])
