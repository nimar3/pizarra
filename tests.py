#  -*- encoding: utf-8 -*-
#  """
#  License: MIT
#  Copyright (c) 2020 - Pizarra
#  """
import datetime
import random
import unittest

from app import create_app_web
from app.base.models_jobs import get_kahan_time
from app.base.util import hash_pass, verify_pass, random_string, process_date
from app.home.routes import allowed_file, over_request_limit
from config import config_dict


class TestCases(unittest.TestCase):

    def setUp(self):
        self.app = create_app_web(config_dict['Debug'])

    def test_verify_hashed_password(self):
        password = 'S9c1JkYAZQrXWDyFFNu9'
        self.assertTrue(hash_pass(password), verify_pass(password, hash_pass(password)))

    def test_process_date_none(self):
        self.assertEqual(process_date(None), None)

    def test_process_date_empty_string(self):
        self.assertEqual(process_date(''), None)

    def test_process_date_invalid(self):
        self.assertEqual(process_date('2020/02/30'), None)

    def test_process_date_valid(self):
        self.assertEqual(process_date('2020/02/29'), datetime.datetime(2020, 2, 29, 0, 0))

    def test_allowed_file_invalid(self):
        with self.app.app_context():
            self.assertFalse(allowed_file('virus.exe'))

    def test_allowed_file_empty_to_trim(self):
        self.assertFalse(allowed_file(' '))

    def test_allowed_file_empty(self):
        self.assertFalse(allowed_file(''))

    def test_allowed_file_none(self):
        self.assertFalse(allowed_file(None))

    def test_allowed_file_valid(self):
        with self.app.app_context():
            allowed_extensions = self.app.config['FILE_ALLOWED_EXTENSIONS']
            for extension in allowed_extensions:
                self.assertTrue(allowed_file('file.' + extension))

    def test_random_string_size_random(self):
        number = random.randint(1, 100)
        self.assertEqual(len(random_string(number)), number)

    def test_random_string_size_default(self):
        self.assertEqual(len(random_string()), 60)

    def test_over_request_none(self):
        self.assertTrue(over_request_limit(None))

    def test_over_request_string(self):
        self.assertTrue(over_request_limit(' '))

    def test_over_request_future(self):
        with self.app.app_context():
            self.assertTrue(over_request_limit(datetime.datetime(2030, 1, 1)))

    def test_over_request_one_second_before(self):
        with self.app.app_context():
            time_seconds = self.app.config['TIME_BETWEEN_REQUESTS'] - 1
            self.assertTrue(over_request_limit(datetime.datetime.utcnow() - datetime.timedelta(seconds=time_seconds)))

    def test_over_request_one_second_after(self):
        with self.app.app_context():
            time_seconds = self.app.config['TIME_BETWEEN_REQUESTS'] + 1
            self.assertFalse(over_request_limit(datetime.datetime.utcnow() - datetime.timedelta(seconds=time_seconds)))

    def test_over_request_past(self):
        with self.app.app_context():
            self.assertFalse(over_request_limit(datetime.datetime(2010, 1, 1)))

    def test_get_kahan_time_random_string(self):
        self.assertEqual(get_kahan_time('MGnPU8Xmlq5mXxh3snEB'), 300.0)

    def test_get_kahan_time_none(self):
        self.assertEqual(get_kahan_time(None), 300.0)

if __name__ == '__main__':
    unittest.main()
