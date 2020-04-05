# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

from flask_security import UserMixin, RoleMixin
from sqlalchemy import Boolean, Binary, DateTime, Column, Integer, BigInteger, String, BLOB, ForeignKey
from sqlalchemy.orm import relationship, backref

from app import db, login_manager
from app.base.util import hash_pass


class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    password = Column(Binary)
    active = Column(Boolean(), default=True)
    quota = Column(Integer(), default=1800)
    last_login_at = Column(DateTime())
    last_login_ip = Column(String(100))
    login_count = Column(Integer)
    confirmed_at = Column(DateTime())
    roles = relationship('Role', secondary='role_user', backref=backref('users', lazy='dynamic'))
    teams = relationship('Team', secondary='team_user', backref=backref('users', lazy='dynamic'))
    badges = relationship('Badge', secondary='achievement', backref=backref('users', lazy='dynamic'))
    requests = relationship('Request')

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


class Role(db.Model, RoleMixin):
    __tablename__ = 'role'
    id = Column(Integer(), primary_key=True)
    name = Column(String(80), unique=True)
    description = Column(String(255))


class Team(db.Model):
    __tablename__ = 'team'
    id = Column(Integer(), primary_key=True)
    name = Column(String(80), unique=True)
    group = Column(Integer(), ForeignKey('group.id'))


class Group(db.Model):
    __tablename__ = 'group'
    id = Column(Integer(), primary_key=True)
    name = Column(String(80), unique=True)
    teams = relationship('Team')


class Badge(db.Model):
    __tablename__ = 'badge'
    id = Column(Integer(), primary_key=True)
    name = Column(String(80), unique=True)
    description = Column(String(255))


class Achievement(db.Model):
    __tablename__ = 'achievement'
    id = Column(Integer(), primary_key=True)
    user_id = Column('user_id', Integer(), ForeignKey('user.id'))
    badge_id = Column('badge_id', Integer(), ForeignKey('badge.id'))


class Request(db.Model):
    __tablename__ = 'request'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime())
    status = Column(String(80))
    file_location = Column(String(255))
    assignment_id = Column('assignment_id', Integer(), ForeignKey('assignment.id'))
    team_id = Column('team_id', Integer(), ForeignKey('team.id'))
    user_id = Column('user_id', Integer(), ForeignKey('user.id'))


class Assignment(db.Model):
    __tablename__ = 'assignment'
    id = Column(Integer, primary_key=True)
    start_date = Column(DateTime())
    due_date = Column(DateTime())
    group_id = Column('group_id', Integer(), ForeignKey('group.id'))
    task_id = Column('task_id', Integer(), ForeignKey('task.id'))


class Task(db.Model):
    __tablename__ = 'task'
    id = Column(Integer, primary_key=True)
    name = Column(String(80))
    description = Column(BLOB)
    header = Column(BLOB)
    template = Column(BLOB)
    attachments = relationship('Attachment')


class Attachment(db.Model):
    __tablename__ = 'attachment'
    id = Column(Integer, primary_key=True)
    file_location = Column(String(255))
    task_id = Column('task_id', Integer(), ForeignKey('task.id'))


class Leaderboard(db.Model):
    __tablename__ = 'leaderboard'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime())
    run_time = Column(BigInteger)
    request_id = Column('request_id', Integer(), ForeignKey('request.id'))
    assignment_id = Column('assignment_id', Integer(), ForeignKey('assignment.id'))


class RoleUser(db.Model):
    __tablename__ = 'role_user'
    id = Column(Integer(), primary_key=True)
    user_id = Column('user_id', Integer(), ForeignKey('user.id'))
    role_id = Column('role_id', Integer(), ForeignKey('role.id'))


class TeamUser(db.Model):
    __tablename__ = 'team_user'
    id = Column(Integer(), primary_key=True)
    user_id = Column('user_id', Integer(), ForeignKey('user.id'))
    team_id = Column('team_id', Integer(), ForeignKey('team.id'))


@login_manager.user_loader
def user_loader(id):
    return User.query.filter_by(id=id).first()


@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    user = User.query.filter_by(username=username).first()
    return user if user else None
