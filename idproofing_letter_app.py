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

from flask import Flask
from flask import g, request, render_template, jsonify, url_for
from flask_wtf.csrf import CsrfProtect, generate_csrf
from werkzeug.local import LocalProxy

from idproofing_letter.exceptions import ApiException
from idproofing_letter.forms import NinForm
from idproofing_letter.database import get_userdb, get_proofingdb


app = Flask(__name__)

app.config.from_object('settings.common')
app.config.from_envvar('IDPROOFING_LETTER_SETTINGS', silent=True)

csrf = CsrfProtect(app)
userdb = LocalProxy(get_userdb)
proofingdb = LocalProxy(get_proofingdb)


@app.route('/')
def index():
    # A view for developing, should not be exposed in production
    return render_template('index.html', message='eduid-proofing-letter', form=NinForm())


@app.route('/get-address', methods=['GET', 'POST'])
def get_address():
    # TODO: Authenticate user
    form = NinForm()

    if request.method == 'POST':
        ret = {
            'endpoint': url_for('confirm', _external=True),
            'csrf': generate_csrf(),
            'expected_fields': ''  # Do we want expected_fields?
        }                                                   # Dev
        if form.validate_on_submit():
            # TODO: Lookup official address via Navet and return address for confirmation
            # TODO: Save a  LetterNinProofingUser to proofingdb
            return jsonify(ret)
        raise ApiException(form.nin.errors)
    else:
        # TODO: Get LetterNinProofingUser from proofingdb or None
        # TODO: Return CSRF or a messages declining to send any more letters
        ret = {
            'endpoint': request.url,
            'expected_fields': form._fields.keys(),  # Do we want expected_fields?
            'csrf': generate_csrf()
        }

        return jsonify(ret)


@app.route('/send-letter', methods=['POST'])
def send_letter():
    # TODO: Authenticate user
    # TODO: If user accepted the official address and data saved in db checks out, ask {service_provider} to send letter
    return jsonify({'success': True})


@csrf.error_handler
def csrf_error(reason):
    raise ApiException(message=reason, status_code=400)


@app.errorhandler(ApiException)
def handle_exception(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.teardown_appcontext
def teardown_db(exception):
    _userdb = getattr(g, '_userdb', None)
    if _userdb is not None:
        _userdb.close()
    _proofingdb = getattr(g, '_proofingdb', None)
    if _proofingdb is not None:
        _proofingdb.close()

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])


