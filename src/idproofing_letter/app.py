# -*- coding: utf-8 -*-

from __future__ import absolute_import

from flask import Flask, jsonify
from flask_apispec.extension import FlaskApiSpec
from webargs.flaskparser import parser as webargs_flaskparser
from eduid_common.api.logging import init_logging
from eduid_common.api.exceptions import ApiException
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

    # Set up logging
    init_logging(app)

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

    @webargs_flaskparser.error_handler
    def handle_webargs_exception(error):
        app.logger.error('ApiException {!r}'.format(error))
        raise (ApiException(error.messages, error.status_code))

    @app.errorhandler(ApiException)
    def handle_flask_exception(error):
        app.logger.error('ApiException {!r}'.format(error))
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    if app.config['APISPEC_SPEC']:
        docs = FlaskApiSpec(app)
        docs.register(idproofing_letter_views.get_state)
        docs.register(idproofing_letter_views.send_letter)
        docs.register(idproofing_letter_views.verify_code)

    app.logger.info('Application initialized')
    return app
