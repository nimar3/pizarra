# -*- encoding: utf-8 -*-
"""
License: MIT
"""
from flask_security.utils import _
from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed, FileField
from wtforms import StringField, SelectMultipleField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, InputRequired, ValidationError
from wtforms.widgets import TextArea

from app.base.models import ClassGroup


class AssignmentForm(FlaskForm):
    name = StringField('Name', id='name', validators=[DataRequired()])
    start_date = StringField('Start Date', id='start-date', render_kw={'autocomplete': 'off'})
    due_date = StringField('Due Date', id='due-date', render_kw={'autocomplete': 'off'})
    title = StringField('Title', id='title', validators=[DataRequired()])
    description = StringField('Description', id='description', widget=TextArea(),
                              render_kw={"rows": "10", "cols": "80"},
                              validators=[DataRequired()])
    header = StringField('Template', id='template', widget=TextArea(), render_kw={"rows": "10"},
                         validators=[DataRequired()])
    classgroups = SelectMultipleField('Class Groups', coerce=int, validators=[InputRequired()])
    badges = SelectMultipleField('Badges', coerce=int)

    def validate_due_date(form, field):
        if field.data is not None and form.start_date.data is not None and field.data < form.start_date.data:
            raise ValidationError("End date must not be earlier than start date.")


class UsersUploadForm(FlaskForm):
    classgroup = QuerySelectField('group', query_factory=lambda: ClassGroup.query.all(), validators=[DataRequired()])
    file = FileField('file', validators=[FileRequired(), FileAllowed(['csv'], _('Only CSV file allowed!'))])
