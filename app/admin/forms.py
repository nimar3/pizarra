# -*- encoding: utf-8 -*-
"""
License: MIT
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SelectMultipleField
from wtforms.validators import DataRequired, InputRequired
from wtforms.widgets import TextArea


class AssignmentForm(FlaskForm):
    name = StringField('Name', id='name', validators=[DataRequired()])
    date = StringField('Date', id='date', validators=[DataRequired()])
    title = StringField('Title', id='title', validators=[DataRequired()])
    description = StringField('Description', id='description', widget=TextArea(),
                              render_kw={"rows": "10", "cols": "80"},
                              validators=[DataRequired()])
    header = StringField('Template', id='template', widget=TextArea(), render_kw={"rows": "10"},
                         validators=[DataRequired()])
    classgroups = SelectMultipleField('Class Groups', coerce=int, validators=[InputRequired()])
    badges = SelectMultipleField('Badges', coerce=int, validators=[InputRequired()])
