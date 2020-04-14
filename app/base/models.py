# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2020 - nimar3
"""
from datetime import datetime
from random import randint

from flask_security import UserMixin, RoleMixin
from sqlalchemy import Boolean, Binary, DateTime, Column, Integer, String, ForeignKey, Enum, UnicodeText, Table
from sqlalchemy.orm import relationship, backref

from app import db, login_manager
from app.base.util import hash_pass, random_string
from app.tasks.models import RequestStatus

# many-to-many relationships
classgroups_assignments = Table('_classgroups_assignments', db.Model.metadata,
                                Column('classgroup_id', Integer, ForeignKey('classgroup.id')),
                                Column('assignment_id', Integer, ForeignKey('assignment.id'))
                                )

assignments_badges = Table('_assignments_badges', db.Model.metadata,
                           Column('assignment_id', Integer, ForeignKey('assignment.id')),
                           Column('badge_id', Integer, ForeignKey('badge.id'))
                           )


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
    active = Column(Boolean(), default=True)
    quota = Column(Integer(), default=21600)
    quota_used = Column(Integer(), default=0)
    last_login_at = Column(DateTime())
    last_login_ip = Column(String(100))
    login_count = Column(Integer, default=0)
    registered_at = Column(DateTime())
    avatar = Column(String)
    access_key = Column(String)
    # Relations
    # one-to-many
    requests = relationship('Request', back_populates='user', order_by='desc(Request.timestamp)')
    # many-to-one (bidirectional relationship)
    classgroup_id = Column(Integer, ForeignKey('classgroup.id'))
    classgroup = relationship('ClassGroup', back_populates='students')
    team_id = Column(Integer, ForeignKey('team.id'))
    team = relationship('Team', back_populates='members')
    # many-to-many
    roles = relationship('Role', secondary='user_roles', backref=backref('users', lazy='dynamic'))
    badges = relationship('Badge', secondary='user_badges', backref=backref('users', lazy='dynamic'))

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

        # if avatar is not presnent when creating user we set one at random
        if 'avatar' not in kwargs:
            setattr(self, 'avatar', 'avatar-' + str(randint(1, 18)) + '-256x256.png')

        if 'password' not in kwargs:
            setattr(self, 'password', hash_pass('123'))

        if 'username' not in kwargs or 'username' is None or 'username' is '':
            setattr(self, 'username', kwargs['email'].split('@')[0])

        if 'access_key' not in kwargs:
            setattr(self, 'access_key', random_string())

    def __repr__(self):
        return str(self.username)

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
    id = Column(Integer(), primary_key=True)
    name = Column(String(100), unique=True)
    members = relationship('User', back_populates='team')


class ClassGroup(db.Model):
    """
    Represent a Class or Group in the database
    A Student can be a part of more than one Class or Group
    """
    __tablename__ = 'classgroup'
    id = Column(Integer(), primary_key=True)
    name = Column(String(100), unique=True)
    description = Column(String(255))
    students = relationship('User', back_populates='classgroup')
    assignments = relationship('Assignment', secondary=classgroups_assignments, back_populates='classgroups',
                               order_by='asc(Assignment.due_date)')


class Badge(db.Model):
    """
    Represents a Badge or achievement in the database
    A Student can earn Badges as he completes the Tasks assigned to them
    """
    __tablename__ = 'badge'
    id = Column(Integer(), primary_key=True)
    name = Column(String(100), unique=True)
    title = Column(String(255))
    subtitle = Column(String(255))
    description = Column(String(255))
    background_color = Column(String(100))
    image = Column(String(255))
    assignments = relationship("Assignment", secondary=assignments_badges, back_populates="badges")


class Request(db.Model):
    """
    Represents a Request sent by an User to Solve an Assignment
    """
    __tablename__ = 'request'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime())
    status = Column(Enum(RequestStatus))
    run_time = Column(Integer)
    file_location = Column(String(255))
    output = Column(UnicodeText)
    assignment = relationship('Assignment', back_populates='requests')
    assignment_id = Column('assignment_id', Integer(), ForeignKey('assignment.id'))
    user = relationship('User', back_populates='requests')
    user_id = Column('user_id', String, ForeignKey('user.id'))


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
    start_date = Column(DateTime())
    due_date = Column(DateTime())
    requests = relationship('Request', back_populates='assignment', order_by='desc(Request.timestamp)')
    classgroups = relationship("ClassGroup", secondary=classgroups_assignments, back_populates="assignments")
    badges = relationship("Badge", secondary=assignments_badges, back_populates="assignments")

    @property
    def expires_soon(self):
        """returns True is an assignments is expiring in less than 24 hours"""
        difference = self.due_date - datetime.utcnow()
        return difference.days == 0

    @property
    def expired(self):
        difference = self.due_date - datetime.utcnow()
        """returns True is an assignments is expired"""
        return difference.days < 0


# many-to-many relation tables

class UserRole(db.Model):
    __tablename__ = 'user_roles'
    id = Column(Integer(), primary_key=True)
    user = Column('user_id', Integer(), ForeignKey('user.id'))
    role = Column('role_id', Integer(), ForeignKey('role.id'))


class UserBadge(db.Model):
    __tablename__ = 'user_badges'
    id = Column(Integer(), primary_key=True)
    user_id = Column('user_id', Integer(), ForeignKey('user.id'))
    badge_id = Column('badge_id', Integer(), ForeignKey('badge.id'))


@login_manager.user_loader
def user_loader(id):
    return User.query.filter_by(id=id).first()


@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    user = User.query.filter_by(username=username).first()
    return user if user else None
