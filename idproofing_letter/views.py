# -*- coding: utf-8 -*-

from __future__ import absolute_import

from flask import g, request, render_template, jsonify, url_for
from flask_wtf.csrf import generate_csrf

from eduid_userdb.proofing import LetterNinProofingUserDB, LetterNinProofingUser

from idproofing_letter import app, csrf
from idproofing_letter.exceptions import ApiException
from idproofing_letter.forms import NinForm, AcceptAddressForm

# Dev mocks
from idproofing_letter import celery_mock
from eduid_userdb.testing import MockedUserDB
MOCK_USERDB = MockedUserDB()
MOCK_PROOFINGDB = {}

__author__ = 'lundberg'

@app.route('/')
def index():
    # A view for developing, should not be exposed in production
    return render_template('index.html', message='eduid-proofing-letter', form1=NinForm(), form2=AcceptAddressForm())

@app.route('/db')
def db():
    # A view for developing, should not be exposed in production
    return render_template('db.html', message='eduid-proofing-letter', users=MOCK_PROOFINGDB)


@app.route('/get-address', methods=['GET', 'POST'])
def get_address():
    # TODO: Authenticate user
    user = MOCK_USERDB.get_user('johnsmith@example.com')
    form = NinForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            ret = dict()
            ret.update({
                'endpoint': url_for('send_letter', _external=True),
                'csrf': generate_csrf(),
                'expected_fields': AcceptAddressForm()._fields.keys()  # Do we want expected_fields?
            })
            # TODO: Lookup official address via Navet and return address for confirmation
            ret['official_address'] = celery_mock.get_formatted_address(form.nin.data)
            # TODO: Save a LetterNinProofingUser to proofingdb
            proofing_user = LetterNinProofingUser({
                'user_id': user.user_id,
                'nin': form.nin.data,
                'verification_code': 'abc{!s}'.format(len(MOCK_PROOFINGDB.keys()) + 1)
            })
            app.logger.debug(proofing_user)
            MOCK_PROOFINGDB[len(MOCK_PROOFINGDB.keys()) + 1] = proofing_user.to_dict()
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
    user = MOCK_USERDB.get_user('johnsmith@example.com')
    form = AcceptAddressForm()
    if form.validate_on_submit():
        # TODO: If user accepted the official address and data saved in db checks out,
        for key, proofing_user in MOCK_PROOFINGDB.items():
            if proofing_user['user_id'] == user.user_id:
                mock_db_id = key
                proofing_user = LetterNinProofingUser(proofing_user)
                break
        # TODO: Ask {service_provider} to send letter
        proofing_user.proofing_letter.is_sent = True
        MOCK_PROOFINGDB[mock_db_id] = proofing_user.to_dict()
        success = form.accepted_address.data
    else:
        raise ApiException({'errors': form.errors}, status_code=400)
    return jsonify({'success': success})


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