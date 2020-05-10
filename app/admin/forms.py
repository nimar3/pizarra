# -*- encoding: utf-8 -*-
"""
License: MIT
"""
from flask_security.utils import _
from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed, FileField
from wtforms import StringField, BooleanField, MultipleFileField
from wtforms.ext.sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from wtforms.validators import DataRequired, InputRequired, ValidationError
from wtforms.widgets import TextArea

from app.base.models import ClassGroup, Badge


class AssignmentForm(FlaskForm):
    name = StringField('Name', id='name', validators=[DataRequired()])
    start_date = StringField('Start Date', id='start-date', render_kw={'autocomplete': 'off'})
    due_date = StringField('Due Date', id='due-date', render_kw={'autocomplete': 'off'})
    title = StringField('Title', id='title', validators=[DataRequired()])
    description = StringField('Description', id='description', widget=TextArea(),
                              render_kw={"rows": "10", "cols": "80"}, validators=[DataRequired()])
    makefile = StringField('Makefile', id='makefile', widget=TextArea(), render_kw={"rows": "10"},
                           validators=[DataRequired()])
    execution_script = StringField('Execution Script', id='execution-script', widget=TextArea(),
                                   render_kw={"rows": "10"}, validators=[DataRequired()])
    expected_result = StringField('Expected Result', id='expected-result', widget=TextArea(), render_kw={"rows": "10"},
                                  validators=[DataRequired()])
    points = StringField('Points', id='points')
    show_output = BooleanField('Show Output', id='show-output')
    files = MultipleFileField('Files')
    classgroups = QuerySelectMultipleField('Groups', query_factory=lambda: ClassGroup.query.all(),
                                           validators=[InputRequired()])
    badges = QuerySelectMultipleField('Badges', query_factory=lambda: Badge.query.all())

    def validate_due_date(form, field):
        if field.data is not None and form.start_date.data is not None and field.data < form.start_date.data:
            raise ValidationError("End date must not be earlier than start date.")


class UsersUploadForm(FlaskForm):
    classgroup = QuerySelectField('Group', query_factory=lambda: ClassGroup.query.all(), validators=[DataRequired()])
    file = FileField('File', validators=[FileRequired(), FileAllowed(['csv'], _('Only CSV file allowed!'))])
