# -*- coding: utf-8 -*-

from __future__ import absolute_import


__author__ = 'lundberg'

"""
For more built in configuration options see,
http://flask.pocoo.org/docs/0.10/config/#builtin-configuration-values
"""

DEBUG = False

# Database URIs
IDPROOFING_MONGO_URI = 'mongodb://'
USERDB_MONGO_URI = 'mongodb://'

# Application specific settings
LETTER_WAIT_TIME_HOURS = 336  # 2 weeks

# Celery config
CELERY_CONFIG = {
    'BROKER_URL': 'amqp://',
    'CELERY_RESULT_BACKEND': 'amqp',
    'CELERY_TASK_SERIALIZER': 'json'
}

# Secret key
SECRET_KEY = None

# Logging
LOG_FILE = None
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'INFO'
LOG_MAX_BYTES = 10000
LOG_BACKUP_COUNT = 10

# No CSRF for now
WTF_CSRF_ENABLED = False

EKOPOST_API_URI = 'https://api.ekopost.se'
EKOPOST_API_VERIFY_SSL = 'true'
EKOPOST_API_USER = ''
EKOPOST_API_PW = ''
EKOPOST_DEBUG_PDF = ''
