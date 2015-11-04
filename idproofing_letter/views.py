# -*- coding: utf-8 -*-

from __future__ import absolute_import

from flask import g, request, render_template, jsonify, url_for
from flask_wtf.csrf import CsrfProtect, generate_csrf

from idproofing_letter import app, csrf
from idproofing_letter.exceptions import ApiException
from idproofing_letter.forms import NinForm


__author__ = 'lundberg'

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
            'endpoint': url_for('send_letter', _external=True),
            'csrf': generate_csrf(),
            'expected_fields': ''  # Do we want expected_fields?
        }                                                   # Dev
        if form.validate_on_submit():
            # TODO: Lookup official address via Navet and return address for confirmation
            # TODO: Save a  LetterNinProofingUser to proofingdb
            return jsonify(ret)
        raise ApiException({'errors': form.errors}, status_code=400)
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