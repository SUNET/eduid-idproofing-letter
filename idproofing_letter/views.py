# -*- coding: utf-8 -*-

from __future__ import absolute_import

from flask import request, render_template, jsonify, url_for
from flask_wtf.csrf import generate_csrf

from idproofing_letter import app, db
from idproofing_letter.exceptions import ApiException
from idproofing_letter.forms import NinForm, AcceptAddressForm, VerifyCodeForm
from idproofing_letter.authentication import authenticate
from idproofing_letter.proofing import create_proofing_state, check_state
from idproofing_letter.celery import get_postal_address, format_address

__author__ = 'lundberg'


@app.route('/')
def index():
    # A view for developing, should not be exposed in production
    return render_template('index.html', message='eduid-proofing-letter', form1=NinForm(), form2=AcceptAddressForm(),
                           form3=VerifyCodeForm())


@app.route('/get-state', methods=['GET'])
def get_state():
    user = authenticate(request)
    proofing_state = db.letter_proofing_statedb.get_state_by_user_id(user.user_id, raise_on_missing=False)
    if proofing_state:
        # If a proofing state is found continue the flow
        return jsonify(check_state(proofing_state))
    return jsonify({
        'endpoint': url_for('get_address', _external=True),
        'expected_fields': NinForm()._fields.keys(),  # Do we want expected_fields?
        'csrf': generate_csrf()
    })


@app.route('/get-address', methods=['POST'])
def get_address():
    user = authenticate(request)
    form = NinForm()
    if form.validate_on_submit():
        nin = form.nin.data
        ret = dict(
            endpoint=url_for('send_letter', _external=True),
            csrf=generate_csrf(),
            expected_fields=AcceptAddressForm()._fields.keys()  # Do we want expected_fields?
        )
        # TODO: Lookup official address via Navet and return address for confirmation
        address = get_postal_address(nin)
        if not address:
            raise ApiException('No address found', status_code=400)
        ret['official_address'] = format_address(address)
        # TODO: Save a LetterNinProofingUser to proofingdb
        proofing_state = create_proofing_state(user.user_id, nin)
        proofing_state.proofing_letter.address = address
        proofingdb.save(proofing_state)
        return jsonify(ret)
    else:
        raise ApiException({'errors': form.errors}, status_code=400)


@app.route('/send-letter', methods=['POST'])
def send_letter():
    user = authenticate(request)
    form = AcceptAddressForm()
    if form.validate_on_submit():
        if not form.accepted_address.data:
            raise ApiException({'success': False, 'reason': 'User declined address'}, status_code=200)
        proofing_state = db.letter_proofing_statedb.get_state_by_user_id(user.user_id)
        if proofing_state.proofing_letter.is_sent:
            raise ApiException({'success': False, 'reason': 'Letter already sent'}, status_code=200)
        # User accepted the official address and data saved in db checks out
        # TODO: ask {service_provider} to send letter
        # TODO: Get result and transaction id from letter service
        proofing_state.proofing_letter.transaction_id = 'bogus transaction id'
        proofing_state.proofing_letter.is_sent = True
        proofing_state.proofing_letter.sent_ts = True
        db.letter_proofing_statedb.save(proofing_state)
        return jsonify(check_state(proofing_state))
    else:
        raise ApiException({'errors': form.errors}, status_code=400)


@app.route('/verify-code', methods=['POST'])
def verify_code():
    user = authenticate(request)
    form = VerifyCodeForm()
    if form.validate_on_submit():
        proofing_state = db.letter_proofing_statedb.get_state_by_user_id(user.user_id)
        if not form.verification_code.data == proofing_state.nin.verification_code:
            raise ApiException({'success': False, 'reason': 'Verification code does not match'}, status_code=200)
        proofing_state.nin.verified = True
        proofing_state.nin.verified_by = 'eduid-idproofing-letter'
        proofing_state.nin.verified_ts = True
        # TODO: Create a JWT and send required data to a Proofing Assertion Consumer
        # Remove proofing user
        db.letter_proofing_statedb.remove_document({'user_id': proofing_state.user_id})
        return jsonify({'success': True})
    else:
        raise ApiException({'errors': form.errors}, status_code=400)


