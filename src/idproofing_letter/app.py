# -*- coding: utf-8 -*-

from __future__ import absolute_import

from flask import Flask, jsonify
from webargs.flaskparser import parser as webargs_flaskparser
from eduid_common.api.logging import init_logging
from eduid_common.api.exceptions import init_exception_handlers
from eduid_userdb import UserDB
from eduid_userdb.proofing import LetterProofingStateDB
from idproofing_letter.ekopost import Ekopost
from idproofing_letter.msg import init_celery

__author__ = 'lundberg'


def init_idproofing_letter_app(name, config=None):
    """
    :param name: The name of the instance, it will affect the configuration loaded.
    :param config: any additional configuration settings. Specially useful
                   in test cases

    :type name: str
    :type config: dict

    :return: the flask app
    :rtype: flask.Flask
    """
    app = Flask(name, static_folder=None)

    # Load configuration
    app.config.from_object('idproofing_letter.settings.common')
    app.config.from_envvar('IDPROOFING_LETTER_SETTINGS', silent=True)
    if config:
        app.config.update(config)

    # Setup logging
    app = init_logging(app)

    # Setup exception handling
    app = init_exception_handlers(app)

    # Register views
    from idproofing_letter.views import idproofing_letter_views
    app.register_blueprint(idproofing_letter_views)

    # Init dbs
    app.central_userdb = UserDB(app.config['MONGO_URI'], 'eduid_am')
    app.proofing_statedb = LetterProofingStateDB(app.config['MONGO_URI'])

    # Init celery
    init_celery(app)

    # Initiate external modules
    app.ekopost = Ekopost(app)

    # Check for secret key
    if app.config['SECRET_KEY'] is None:
        app.logger.error('Missing SECRET_KEY in the settings file')

    app.logger.info('Application initialized')
    return app
