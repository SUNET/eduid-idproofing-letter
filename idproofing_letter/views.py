# -*- coding: utf-8 -*-

from __future__ import absolute_import

from flask import request, render_template, jsonify, url_for
from flask_wtf.csrf import generate_csrf

from datetime import datetime, timedelta

from eduid_userdb.proofing import LetterNinProofingUser

from idproofing_letter import app, userdb, proofingdb
from idproofing_letter.exceptions import ApiException
from idproofing_letter.forms import NinForm, AcceptAddressForm, VerifyCodeForm
from idproofing_letter.authentication import authenticate
from idproofing_letter.proofing import create_proofing_user, check_user_status


# Dev mocks
from idproofing_letter import celery_mock

__author__ = 'lundberg'


@app.route('/')
def index():
    # A view for developing, should not be exposed in production
    return render_template('index.html', message='eduid-proofing-letter', form1=NinForm(), form2=AcceptAddressForm())


@app.route('/get-address', methods=['GET', 'POST'])
def get_address():
    user = authenticate(request)
    proofing_user = proofingdb.get_user_by_id(user.user_id, raise_on_missing=False)

    form = NinForm()

    if not proofing_user:
        if form.validate_on_submit():
            nin = form.nin.data
            ret = dict(
                endpoin=url_for('send_letter', _external=True),
                csrf=generate_csrf(),
                expected_fields=AcceptAddressForm()._fields.keys()  # Do we want expected_fields?
            )
            # TODO: Lookup official address via Navet and return address for confirmation
            ret['official_address'] = celery_mock.get_formatted_address(nin)
            # TODO: Save a LetterNinProofingUser to proofingdb
            proofing_user = create_proofing_user(user.user_id, nin)
            proofingdb.save(proofing_user, user_id_attr='user_id')
            return jsonify(ret)
        raise ApiException({'errors': form.errors}, status_code=400)
    else:  # GET
        ret = check_user_status(proofing_user)
        if ret:
            return jsonify(ret)



        return jsonify(ret)


@app.route('/send-letter', methods=['POST'])
def send_letter():
    # TODO: Authenticate user
    user = userdb.get_user_by_eppn(app.config['DEV_EPPN'])
    form = AcceptAddressForm()
    if form.validate_on_submit():
        # TODO: If user accepted the official address and data saved in db checks out,
        proofing_user = proofingdb.get_user_by_id(user.user_id)
        # TODO: Ask {service_provider} to send letter
        proofing_user.proofing_letter.is_sent = True
        proofing_user.proofing_letter.sent_ts = True
        proofingdb.save(proofing_user, user_id_attr='user_id')
        success = form.accepted_address.data
    else:
        raise ApiException({'errors': form.errors}, status_code=400)
    return jsonify({'success': success})


@app.route('/verify-code', methods=['POST'])
def verify_code():
    # TODO: Authenticate user
    user = userdb.get_user_by_eppn(app.config['DEV_EPPN'])
    form = VerifyCodeForm()
    if form.validate_on_submit():
        return jsonify({'success': True})


