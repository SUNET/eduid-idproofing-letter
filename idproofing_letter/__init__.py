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
from flask_wtf.csrf import CsrfProtect
from eduid_common.api.database import ApiDatabase

from idproofing_letter.exceptions import ApiException
from idproofing_letter.forms import NinForm

import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

app.config.from_object('idproofing_letter.settings.common')
app.config.from_envvar('IDPROOFING_LETTER_SETTINGS', silent=True)

csrf = CsrfProtect(app)
db = ApiDatabase(app)
# Set up logging
handler = RotatingFileHandler(app.config['LOG_FILE'], maxBytes=app.config['LOG_MAX_BYTES'],
                              backupCount=app.config['LOG_BACKUP_COUNT'])
handler.setLevel(app.config['LOG_LEVEL'])
formatter = logging.Formatter(app.config['LOG_FORMAT'])
handler.setFormatter(formatter)
app.logger.addHandler(handler)


@csrf.error_handler
def csrf_error(reason):
    raise ApiException(message=reason, status_code=400)


@app.errorhandler(ApiException)
def handle_exception(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response



# views needs to be imported after app init due to circular dependency
import idproofing_letter.views
