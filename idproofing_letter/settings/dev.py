# -*- coding: utf-8 -*-

from __future__ import absolute_import

__author__ = 'lundberg'

DEBUG = True

MONGO_URI = 'mongodb://eduid_idproofing_letter:eduid_idproofing_letter_pw@mongodb.docker'

CELERY_CONFIG = {
    'BROKER_URL': 'amqp://eduid:eduid_pw@rabbitmq.docker/msg',
    'CELERY_RESULT_BACKEND': 'amqp',
    'CELERY_TASK_SERIALIZER': 'json',
}

LOG_LEVEL = 'DEBUG'
