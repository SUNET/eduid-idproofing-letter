# -*- coding: utf-8 -*-

from __future__ import absolute_import

from flask import render_template, jsonify, url_for
from flask_wtf.csrf import generate_csrf

from idproofing_letter import app, db, ekopost, pdf
from eduid_common.api.exceptions import ApiException
from idproofing_letter.forms import NinForm, VerifyCodeForm, GetState
from idproofing_letter.authentication import authenticate
from idproofing_letter.proofing import create_proofing_state, check_state
from idproofing_letter.celery import get_postal_address

__author__ = 'lundberg'


@app.route('/')
def index():
    # A view for developing, should not be exposed in production
    if app.config['DEBUG']:
        return render_template('index.html', message='eduid-proofing-letter', form1=NinForm(), form2=VerifyCodeForm())
    raise ApiException('Not found', status_code=404)


@app.route('/get-state', methods=['POST'])
def get_state():
    form = GetState()
    if form.validate_on_submit():
        user = authenticate(form)
        proofing_state = db.letter_proofing_statedb.get_state_by_user_id(user.user_id, raise_on_missing=False)
        app.logger.info('Getting proofing state for user {!r}'.format(user))
        if proofing_state:
            # If a proofing state is found continue the flow
            return jsonify(check_state(proofing_state))
        return jsonify({
         'endpoint': url_for('send_letter', _external=True),
         'expected_fields': NinForm()._fields.keys(),  # Do we want expected_fields?
         'csrf': generate_csrf()
        })
    else:
        app.logger.error('ApiException {!r}'.format(form.errors))
        raise ApiException('Validation error', payload={'errors': form.errors}, status_code=400)


@app.route('/send-letter', methods=['POST'])
def send_letter():
    form = NinForm()
    if form.validate_on_submit():
        user = authenticate(form)
        nin = form.nin.data

        app.logger.info('Sending letter for user {!r}'.format(user))
        proofing_state = db.letter_proofing_statedb.get_state_by_user_id(user.user_id, raise_on_missing=False)

        app.logger.info('Getting address for user {!r}'.format(user))
        app.logger.debug('NIN: {!s}'.format(nin))
        # Lookup official address via Navet
        address = get_postal_address(nin)
        if not address:
            app.logger.error('No address found for user {!r}'.format(user))
            raise ApiException('No address found', status_code=400)
        app.logger.debug('Official address: {!r}'.format(address))

        if not proofing_state:
            # Create a LetterNinProofingUser in proofingdb
            proofing_state = create_proofing_state(user.user_id, nin)
            app.logger.info('Created proofing state for user {!r}'.format(user))

        if proofing_state.proofing_letter.is_sent:
            app.logger.info('User {!r} has already sent a letter'.format(user))
            return jsonify(check_state(proofing_state))

        # Check that user is not trying to register another NIN
        if not proofing_state.nin.number == nin:
            app.logger.error('NIN mismatch for user {!r}'.format(user))
            app.logger.error('Old NIN: {!s}'.format(proofing_state.nin.number))
            app.logger.error('New NIN: {!s}'.format(nin))
            raise ApiException('NIN mismatch', status_code=400)

        # Set or update official address
        proofing_state.proofing_letter.address = address
        db.letter_proofing_statedb.save(proofing_state)

        # User accepted a letter to their official address and data saved in db checks out
        # and therefore we can now create the letter as a PDF-document and send it.
        if app.config.get("EKOPOST_DEBUG_PDF", None):
            pdf.create_pdf(proofing_state.proofing_letter.address,
                           proofing_state.nin.verification_code)
            campaign_id = 'debug mode transaction id'
        else:
            pdf_letter = pdf.create_pdf(proofing_state.proofing_letter.address,
                                        proofing_state.nin.verification_code)
            try:
                campaign_id = ekopost.send(user.eppn, pdf_letter)
            except ApiException as api_exception:
                app.logger.error('ApiException {!r}'.format(api_exception.message))
                raise api_exception

        proofing_state.proofing_letter.transaction_id = campaign_id
        proofing_state.proofing_letter.is_sent = True
        proofing_state.proofing_letter.sent_ts = True
        db.letter_proofing_statedb.save(proofing_state)
        return jsonify(check_state(proofing_state))
    else:
        app.logger.error('ApiException {!r}'.format(form.errors))
        raise ApiException('Validation error', payload={'errors': form.errors}, status_code=400)


@app.route('/verify-code', methods=['POST'])
def verify_code():
    form = VerifyCodeForm()
    if form.validate_on_submit():
        user = authenticate(form)
        app.logger.info('Verifying code for user {!r}'.format(user))
        proofing_state = db.letter_proofing_statedb.get_state_by_user_id(user.user_id)
        if not form.verification_code.data == proofing_state.nin.verification_code:
            app.logger.error('Verification code for user {!r} does not match'.format(user))
            # TODO: Throttling to discourage an adversary to try brute force
            raise ApiException('Verification code does not match', payload={'success': False},
                               status_code=200)
        proofing_state.nin.is_verified = True
        proofing_state.nin.verified_by = 'eduid-idproofing-letter'
        proofing_state.nin.verified_ts = True
        # TODO: Create a JWT and send required data to a Proofing Assertion Consumer
        app.logger.info('Verified code for user {!r}'.format(user))
        data = proofing_state.nin.to_dict()
        data['official_address'] = proofing_state.proofing_letter.address
        data['transaction_id'] = proofing_state.proofing_letter.transaction_id
        ret = {'success': True, 'data': data}
        # Remove proofing user
        db.letter_proofing_statedb.remove_document({'user_id': proofing_state.user_id})
        return jsonify(ret)
    else:
        app.logger.error('ApiException {!r}'.format(form.errors))
        raise ApiException(payload={'errors': form.errors}, status_code=400)


