# -*- coding: utf-8 -*-

from __future__ import absolute_import
from os.path import abspath, dirname, join, normpath

__author__ = 'lundberg'

"""
For more built in configuration options see,
http://flask.pocoo.org/docs/0.10/config/#builtin-configuration-values
"""

DEBUG = False

# Absolute filesystem path to the Flask project directory:
PROJECT_ROOT = dirname(dirname(dirname(abspath(__file__))))

# Absolute filesystem path to the secret file which holds this project's
# SECRET_KEY. Will be auto-generated the first time this file is interpreted.
SECRET_FILE = normpath(join(PROJECT_ROOT, 'SECRET'))

# Try to load the SECRET_KEY from our SECRET_FILE. If that fails, then generate
# a random SECRET_KEY and save it into our SECRET_FILE for future loading. If
# everything fails, then just raise an exception.
try:
    SECRET_KEY = open(SECRET_FILE).read().strip()
except IOError:
    try:
        with open(SECRET_FILE, 'w') as f:
            import random
            choice = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
            SECRET_KEY = ''.join([random.SystemRandom().choice(choice) for i in range(50)])
            f.write(SECRET_KEY)
    except IOError:
        raise Exception('Cannot open file `%s` for writing.' % SECRET_FILE)

# Database URIs
IDPROOFING_MONGO_URI = 'mongodb://'
USERDB_MONGO_URI = 'mongodb://'

# Application specific settings
LETTER_WAIT_TIME_HOURS = 1# 336  # 2 weeks
