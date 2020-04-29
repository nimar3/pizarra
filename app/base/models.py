# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2020 - nimar3
"""
from datetime import datetime
from random import randint

from flask import current_app
from flask_security import UserMixin, RoleMixin
from sqlalchemy import Boolean, Binary, DateTime, Column, Integer, String, ForeignKey, Enum, UnicodeText, Table, JSON, \
    Float
from sqlalchemy.orm import relationship, backref

from app import db, login_manager
from app.base.models_tasks import RequestStatus
from app.base.util import hash_pass, random_string, process_date

# many-to-many relationships
classgroups_assignments = Table('_classgroups_assignments', db.Model.metadata,
                                Column('classgroup_id', Integer, ForeignKey('classgroup.id')),
                                Column('assignment_id', Integer, ForeignKey('assignment.id'))
                                )

assignments_badges = Table('_assignments_badges', db.Model.metadata,
                           Column('assignment_id', Integer, ForeignKey('assignment.id')),
                           Column('badge_id', Integer, ForeignKey('badge.id'))
                           )

users_roles = Table('_users_roles', db.Model.metadata,
                    Column('user_id', Integer(), ForeignKey('user.id')),
                    Column('role_id', Integer(), ForeignKey('role.id'))
                    )


class UserBadge(db.Model):
    __tablename__ = '_users_badges'
    id = Column(Integer, primary_key=True)
    user_id = Column('user_id', Integer(), ForeignKey('user.id'))
    badge_id = Column('badge_id', Integer(), ForeignKey('badge.id'))
    timestamp = Column('timestamp', DateTime(), default=datetime.now)


class User(db.Model, UserMixin):
    """
    Represents the Users of the application in the database
    """
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    name = Column(String)
    password = Column(Binary)
    active = Column(Boolean, default=True)
    quota = Column(Integer, default=21600)
    quota_used = Column(Integer, default=0)
    last_login_at = Column(DateTime)
    last_login_ip = Column(String(100))
    login_count = Column(Integer, default=0)
    registered_at = Column(DateTime, default=datetime.utcnow)
    last_request_sent_at = Column(DateTime)
    avatar = Column(String)
    access_token = Column(String)
    points = Column(Integer, default=0)
    # Relations
    # one-to-many
    requests = relationship('Request', back_populates='user', order_by='desc(Request.timestamp)',
                            cascade='all, delete, delete-orphan')
    # many-to-one (bidirectional relationship)
    classgroup_id = Column(Integer, ForeignKey('classgroup.id'))
    classgroup = relationship('ClassGroup', back_populates='students')
    team_id = Column(Integer, ForeignKey('team.id'))
    team = relationship('Team', back_populates='members')
    # many-to-many
    roles = relationship('Role', secondary='_users_roles', backref=backref('users', lazy='dynamic'))
    badges = relationship('Badge', secondary='_users_badges', backref=backref('users', lazy='dynamic'))

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            if key == 'password':
                value = hash_pass(value)  # we need bytes here (not plain str)

            setattr(self, key, value)

        # default values
        if 'avatar' not in kwargs:
            setattr(self, 'avatar', 'avatar-' + str(randint(1, 18)) + '-256x256.png')

        if 'password' not in kwargs:
            setattr(self, 'password', hash_pass(random_string(5)))

        if 'username' not in kwargs or 'username' is None or 'username' is '':
            setattr(self, 'username', generate_username(kwargs['email']))

        if 'access_token' not in kwargs:
            setattr(self, 'access_token', random_string())

        if 'roles' not in kwargs:
            roles = [Role.query.filter_by(name='users').first()]
            setattr(self, 'roles', roles)

    def __repr__(self):
        return '{}, {} ({})'.format(self.name, self.email, self.username)

    @property
    def quota_percentage_used(self):
        return round((self.quota_used * 100) / self.quota, 2)

    @property
    def request_percentage_passed(self):
        request_total = len(self.requests)
        requests_finished = len(list(filter(lambda request: request.status is RequestStatus.FINISHED, self.requests)))
        return 0 if request_total == 0 else round((requests_finished * 100) / request_total, 2)

    @property
    def passed_assignments(self):
        finished_requests = list(filter(lambda request: request.status is RequestStatus.FINISHED, self.requests))
        return set(x.assignment.id for x in finished_requests)

    @property
    def is_admin(self):
        return self.has_role('admins')


class Role(db.Model, RoleMixin):
    """
    Represents the Roles of the users in the database
    """
    __tablename__ = 'role'
    id = Column(Integer(), primary_key=True)
    name = Column(String(100), unique=True)
    description = Column(String(255))


class Team(db.Model):
    """
    Represents a Team of students in the database
    A Student can be a part of many teams (in case he is part of more than one Group)
    A Team can have many students
    """
    __tablename__ = 'team'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    key = Column(String)
    members = relationship('User', back_populates='team')

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        if 'key' not in kwargs:
            setattr(self, 'key', random_string(10))


class ClassGroup(db.Model):
    """
    Represent a Class or Group in the database
    A Student can be a part of more than one Class or Group
    """
    __tablename__ = 'classgroup'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)
    description = Column(String(255))
    students = relationship('User', back_populates='classgroup', cascade='all, delete, delete-orphan')
    assignments = relationship('Assignment', secondary=classgroups_assignments, back_populates='classgroups',
                               order_by='asc(Assignment.due_date)')

    def __repr__(self):
        return '{} ({})'.format(self.description, self.name)


class Badge(db.Model):
    """
    Represents a Badge or achievement in the database
    A Student can earn Badges as he completes the Tasks assigned to them
    """
    __tablename__ = 'badge'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    title = Column(String)
    subtitle = Column(String)
    description = Column(String)
    rule = Column(UnicodeText)
    points = Column(Integer)
    image = Column(String)
    background_color = Column(String)
    assignments = relationship("Assignment", secondary=assignments_badges, back_populates="badges")

    def __repr__(self):
        return '{} - {}'.format(self.title, self.subtitle)


class Request(db.Model):
    """
    Represents a Request sent by an User to Solve an Assignment
    """
    __tablename__ = 'request'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime(), default=datetime.utcnow)
    status = Column(Enum(RequestStatus))
    run_time = Column(Float)
    file_location = Column(String)
    code_analysis = Column(JSON)
    output = Column(UnicodeText)
    ip_address = Column(String)
    task_id = Column(String)
    points_assigned = Column(Integer)
    assignment = relationship('Assignment', back_populates='requests')
    assignment_id = Column('assignment_id', Integer, ForeignKey('assignment.id'))
    user = relationship('User', back_populates='requests')
    user_id = Column('user_id', Integer, ForeignKey('user.id'))

    @property
    def finished_execution(self):
        return self.status in [RequestStatus.CANCELED, RequestStatus.ERROR, RequestStatus.TIMEWALL,
                               RequestStatus.FINISHED]

    @property
    def max_execution_time(self):
        return current_app.config['TIMEWALL'] if self.assignment.timewall is None else min(
            current_app.config['TIMEWALL'], self.assignment.timewall)

    def __repr__(self):
        return 'Request: {} from {} for Assignment {}'.format(self.id, self.user, self.assignment)


class Assignment(db.Model):
    """
    Represent an Assigment to complete by the Class or Group in the database
    """
    __tablename__ = 'assignment'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    title = Column(String(100))
    description = Column(UnicodeText)
    header = Column(UnicodeText)
    start_date = Column(DateTime)
    due_date = Column(DateTime)
    points = Column(Integer, default=100)
    show_output = Column(Boolean, default=True)
    timewall = Column(Float)
    requests = relationship('Request', back_populates='assignment', order_by='desc(Request.timestamp)',
                            cascade='delete')
    classgroups = relationship("ClassGroup", secondary=classgroups_assignments, back_populates="assignments")
    badges = relationship("Badge", secondary=assignments_badges, back_populates="assignments")

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if (key == 'start_date' or key == 'due_date') and isinstance(value, str):
                value = process_date(value)

            setattr(self, key, value)

    @property
    def expires_soon(self):
        """returns True is an assignments is expiring in less than 24 hours"""
        if self.due_date is None:
            return False
        else:
            difference = self.due_date - datetime.utcnow()
            return self.due_date > datetime.utcnow() and difference.days == 0

    @property
    def expired(self):
        """returns True if an assignment is expired"""
        return self.due_date is not None and self.due_date < datetime.utcnow()

    @property
    def started(self):
        """returns True if an assignment started"""
        return self.start_date is None or self.start_date < datetime.utcnow()

    def __repr__(self):
        return '{} - {}'.format(self.name, self.title)


@login_manager.user_loader
def user_loader(id):
    return User.query.filter_by(id=id).first()


@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    user = User.query.filter_by(username=username).first()
    return user if user else None


def generate_username(email):
    """
    generates an username based on the email. If the username is duplicated it will try to generate a new one with
    username.N where N is incremental until no user is found
    """
    username = email.split('@')[0]
    if User.query.filter_by(username=username).first() is None:
        return username
    else:
        # try to generate a random username
        i = 0
        while True:
            random_username = '.'.join([username, str(i)])
            if User.query.filter_by(username=random_username).first() is None:
                return random_username
            else:
                i += 1
