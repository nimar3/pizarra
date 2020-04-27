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

from dateutil.parser import parse
from flask import url_for, redirect, request, abort
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


def verify_is_admin():
    """Redirects users that are not admin"""
    if not current_user.is_authenticated or not current_user.is_admin:
        return abort(403)


def is_allowed_anonymous_path(path, method):
    """Checks if a given path and method is allowed for accessing without being authenticated"""
    allowed_regex_paths = [['/assignments/.*', ['POST']]]
    for item in allowed_regex_paths:
        regex_path, allowed_methods = item[0], item[1]
        pattern = re.compile(regex_path)
        if pattern.match(path) and method in allowed_methods:
            return True

    return False


def process_date(string_date):
    """ transforms a string date to datetime """
    if string_date is not None and string_date != '':
        try:
            parsed_date = parse(string_date)
            return parsed_date
        except ValueError:
            pass

    return None


def remove_comments(source_code):
    """
    remove comments from C and C++ comments, modified to keep new lines so line numbers don't change
    http://stackoverflow.com/questions/241327/python-snippet-to-remove-c-and-c-comments
    """

    def replacer(match):
        s = match.group(0)
        if s.startswith('/'):
            return " " + "\n" * s.count('\n')  # note: a space and not an empty string
        else:
            return s

    pattern = re.compile(
        r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
        re.DOTALL | re.MULTILINE
    )

    return re.sub(pattern, replacer, source_code)
