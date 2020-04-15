# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

import binascii
import hashlib
import os
# Inspiration -> https://www.vitoshacademy.com/hashing-passwords-in-python/
import random
import re
import string

from flask import url_for, redirect, request
from flask_login import current_user


def hash_pass(password):
    """Hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'),
                                  salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash)  # return bytes


def verify_pass(provided_password, stored_password):
    """Verify a stored password against one provided by user"""
    stored_password = stored_password.decode('ascii')
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512',
                                  provided_password.encode('utf-8'),
                                  salt.encode('ascii'),
                                  100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password


def random_string(size=60):
    """Generates a random alphanumeric string for a given size"""
    return ''.join(random.choice(string.ascii_letters + string.digits) for i in range(size))


def verify_logged_in():
    """Redirects users that are trying to access private areas"""
    if not current_user.is_authenticated and not is_allowed_anonymous_path(request.path, request.method):
        return redirect(url_for('base_blueprint.login'))


def is_allowed_anonymous_path(path, method):
    """Checks if a given path and method is allowed for accessing without being authenticated"""
    allowed_regex_paths = [['/assignments/.*', ['POST']]]
    for item in allowed_regex_paths:
        regex_path, allowed_methods = item[0], item[1]
        pattern = re.compile(regex_path)
        if pattern.match(path) and method in allowed_methods:
            return True

    return False
