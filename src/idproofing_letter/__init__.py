# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 NORDUnet A/S
# All rights reserved.
#
#   Redistribution and use in source and binary forms, with or
#   without modification, are permitted provided that the following
#   conditions are met:
#
#     1. Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#     2. Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided
#        with the distribution.
#     3. Neither the name of the NORDUnet nor the names of its
#        contributors may be used to endorse or promote products derived
#        from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

from __future__ import absolute_import

from flask import Flask, jsonify
from flask_apispec.extension import FlaskApiSpec
from webargs.flaskparser import parser as webargs_flaskparser
from eduid_common.api.database import ApiDatabase
from eduid_common.api.json_encoder import EduidJSONEncoder
from eduid_common.api.exceptions import ApiException
from idproofing_letter.ekopost import Ekopost

import logging
from logging.handlers import RotatingFileHandler

__import__('pkg_resources').declare_namespace(__name__)

# Initiate application
app = Flask(__name__, static_folder=None)

# Setup JSON encoding
app.json_encoder = EduidJSONEncoder

# Load configuration
app.config.from_object('idproofing_letter.settings.common')
app.config.from_envvar('IDPROOFING_LETTER_SETTINGS', silent=True)

# Initiate external modules
db = ApiDatabase(app)
ekopost = Ekopost(app)

# Set up logging
try:
    handler = RotatingFileHandler(app.config['LOG_FILE'], maxBytes=app.config['LOG_MAX_BYTES'],
                                  backupCount=app.config['LOG_BACKUP_COUNT'])
    handler.setLevel(app.config['LOG_LEVEL'])
    formatter = logging.Formatter(app.config['LOG_FORMAT'])
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
except AttributeError:
    app.logger.info('Logging not set up')
    app.logger.info('Missing LOG_FILE in the settings file')

# Check for secret key
if app.config['SECRET_KEY'] is None:
    app.logger.error('Missing SECRET_KEY in the settings file')


@webargs_flaskparser.error_handler
def handle_webargs_exception(error):
    app.logger.error('ApiException {!r}'.format(error))
    raise(ApiException(error.messages, error.status_code))


@app.errorhandler(ApiException)
def handle_flask_exception(error):
    app.logger.error('ApiException {!r}'.format(error))
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


# views needs to be imported after app init due to circular dependency
from idproofing_letter import views

if app.config['APISPEC_SPEC']:
    docs = FlaskApiSpec(app)
    docs.register(views.get_state)
    docs.register(views.send_letter)
    docs.register(views.verify_code)

app.logger.info('Application started')
