# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2020 - nimar3
"""

from flask_security import UserMixin, RoleMixin
from sqlalchemy import Boolean, Binary, DateTime, Column, Integer, String, BLOB, ForeignKey, Enum, Table
from sqlalchemy.orm import relationship, backref

from app import db, login_manager
from app.base.util import hash_pass
from app.tasks.models import RequestStatus

classgroup_assignments = Table('_classgroup_assignments', db.Model.metadata,
                               Column('classgroup_id', Integer, ForeignKey('classgroup.id')),
                               Column('assignment_id', Integer, ForeignKey('assignment.id'))
                               # TODO fix this problem with duplicated keys
                               # PrimaryKeyConstraint('classgroup_id', 'assignment_id'),
                               )


class User(db.Model, UserMixin):
    """
    Represents the Users of the application in the database
    """
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    password = Column(Binary)
    active = Column(Boolean(), default=True)
    quota = Column(Integer(), default=21600)
    quota_used = Column(Integer(), default=0)
    last_login_at = Column(DateTime())
    last_login_ip = Column(String(100))
    login_count = Column(Integer, default=0)
    registered_at = Column(DateTime())
    avatar = Column(String, default='default-user-128x128.jpg')
    requests = relationship('Request', back_populates='user')
    roles = relationship('Role', secondary='user_roles', backref=backref('users', lazy='dynamic'))
    classgroups = relationship('ClassGroup', secondary='user_classgroups', backref=backref('users', lazy='dynamic'))
    teams = relationship('Team', secondary='user_teams', backref=backref('users', lazy='dynamic'))
    badges = relationship('Badge', secondary='user_badges', backref=backref('users', lazy='dynamic'))

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            if property == 'password':
                value = hash_pass(value)  # we need bytes here (not plain str)

            setattr(self, property, value)

    def __repr__(self):
        return str(self.username)

    @property
    def assignments(self):
        classgroups_ids = [classgroup.id for classgroup in self.classgroups]
        return Assignment.query.filter(Assignment.id.in_(classgroups_ids)).all()

    @property
    def quota_percentage_used(self):
        return round((self.quota_used * 100) / self.quota, 2)

    @property
    def request_percentage_passed(self):
        request_total = len(self.requests)
        requests_finished = len(list(filter(lambda request: request.status is RequestStatus.FINISHED, self.requests)))
        return 0 if request_total == 0 else round((requests_finished * 100) / request_total, 2)


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


class ClassGroup(db.Model):
    """
    Represent a Class or Group in the database
    A Student can be a part of more than one Class or Group
    """
    __tablename__ = 'classgroup'
    id = Column(Integer(), primary_key=True)
    name = Column(String(100), unique=True)
    description = Column(String(255))
    assignments = relationship('Assignment', secondary='_classgroup_assignments',
                               backref=backref('classgroups', lazy='dynamic'))


class Badge(db.Model):
    """
    Represents a Badge or achievement in the database
    A Student can earn Badges as he completes the Tasks assigned to them
    """
    __tablename__ = 'badge'
    id = Column(Integer(), primary_key=True)
    name = Column(String(100), unique=True)
    image = Column(String(255))
    title = Column(String(255))
    subtitle = Column(String(255))
    description = Column(String(255))


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
    output = Column(BLOB)
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
    description = Column(BLOB)
    header = Column(BLOB)
    template = Column(BLOB)
    start_date = Column(DateTime())
    due_date = Column(DateTime())
    requests = relationship('Request', back_populates='assignment')
    attachments = relationship('Attachment')
    classgroup = relationship(
        'ClassGroup',
        secondary='_classgroup_assignments',
        back_populates='assignments')


class Attachment(db.Model):
    """
    Represent an Attachment from an Assignment in the database
    """
    __tablename__ = 'attachment'
    id = Column(Integer, primary_key=True)
    file_location = Column(String(255))
    assignment = Column('assignment_id', Integer(), ForeignKey('assignment.id'))


# many-to-many relation tables

class UserRole(db.Model):
    __tablename__ = 'user_roles'
    id = Column(Integer(), primary_key=True)
    user = Column('user_id', Integer(), ForeignKey('user.id'))
    role = Column('role_id', Integer(), ForeignKey('role.id'))


class UserClassGroup(db.Model):
    __tablename__ = 'user_classgroups'
    id = Column(Integer(), primary_key=True)
    user_id = Column('user_id', Integer(), ForeignKey('user.id'))
    classgroup = Column('classgroup_id', Integer(), ForeignKey('classgroup.id'))


class UserTeam(db.Model):
    __tablename__ = 'user_teams'
    id = Column(Integer(), primary_key=True)
    user_id = Column('user_id', Integer(), ForeignKey('user.id'))
    team_id = Column('team_id', Integer(), ForeignKey('team.id'))


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
