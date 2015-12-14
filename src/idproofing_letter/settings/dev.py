# -*- coding: utf-8 -*-

from __future__ import absolute_import

from os.path import abspath, dirname, join, normpath

__author__ = 'lundberg'

DEBUG = True

# Absolute filesystem path to the Flask project directory:
PROJECT_ROOT = dirname(dirname(dirname(dirname(abspath(__file__)))))

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

MONGO_URI = 'mongodb://eduid_idproofing_letter:eduid_idproofing_letter_pw@mongodb.docker'

CELERY_CONFIG = {
    'BROKER_URL': 'amqp://eduid:eduid_pw@rabbitmq.docker/msg',
    'CELERY_RESULT_BACKEND': 'amqp',
    'CELERY_TASK_SERIALIZER': 'json',
}

EKOPOST_API_URI = 'http://api.sandbox.ekopost.se'
EKOPOST_API_VERIFY_SSL = 'false'
EKOPOST_API_USER = ''
EKOPOST_API_PW = ''
EKOPOST_DEBUG_PDF = join(PROJECT_ROOT, 'pdfs/letter.pdf')

LOG_FILE = join(PROJECT_ROOT, 'logs/idproofing_letter.log')
LOG_LEVEL = 'DEBUG'
