# -*- encoding: utf-8 -*-
"""
License: MIT
"""

from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectMultipleField
from wtforms.validators import DataRequired, InputRequired


class AssignmentForm(FlaskForm):
    name = StringField('Name', id='name', validators=[DataRequired()])
    title = StringField('Title', id='title', validators=[DataRequired()])
    description = StringField('Description', id='description', validators=[DataRequired()])
    header = StringField('Header', id='header', validators=[DataRequired()])
    template = StringField('Template', id='template', validators=[DataRequired()])
    classgroups = SelectMultipleField('Class Groups', coerce=int, validators=[InputRequired()])
    start_date = DateField('StartDate', id='start_date', validators=[DataRequired()])
    due_date = DateField('DueDate', id='due_date', validators=[DataRequired()])
