# -*- coding: utf-8 -*-

from __future__ import absolute_import

from flask import request, render_template, jsonify, url_for
from flask_wtf.csrf import generate_csrf

from idproofing_letter import app, db, ekopost, pdf
from idproofing_letter.exceptions import ApiException
from idproofing_letter.forms import NinForm, AcceptAddressForm, VerifyCodeForm, GetState
from idproofing_letter.authentication import authenticate
from idproofing_letter.proofing import create_proofing_state, check_state
from idproofing_letter.celery import get_postal_address, format_address

__author__ = 'lundberg'


@app.route('/')
def index():
    # A view for developing, should not be exposed in production
    if app.config['DEBUG']:
        return render_template('index.html', message='eduid-proofing-letter', form1=NinForm(),
                               form2=AcceptAddressForm(), form3=VerifyCodeForm())
    raise ApiException({'errors': 'Not found'}, status_code=404)


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
         'endpoint': url_for('get_address', _external=True),
         'expected_fields': NinForm()._fields.keys(),  # Do we want expected_fields?
         'csrf': generate_csrf()
        })
    else:
        app.logger.error('ApiException {!r}'.format(form.errors))
        raise ApiException({'errors': form.errors}, status_code=400)


@app.route('/get-address', methods=['POST'])
def get_address():
    form = NinForm()
    if form.validate_on_submit():
        user = authenticate(form)
        proofing_state = db.letter_proofing_statedb.get_state_by_user_id(user.user_id, raise_on_missing=False)
        nin = form.nin.data
        app.logger.info('Getting address for user {!r}'.format(user))
        app.logger.debug('NIN: {!s}'.format(nin))
        # Lookup official address via Navet and return address for confirmation
        address = get_postal_address(nin)
        if not address:
            app.logger.error('No address found for user {!r}'.format(user))
            raise ApiException('No address found', status_code=400)
        app.logger.debug('Official address: {!r}'.format(address))
        ret = dict(
            endpoint=url_for('send_letter', _external=True),
            csrf=generate_csrf(),
            expected_fields=AcceptAddressForm()._fields.keys()  # Do we want expected_fields?
        )
        ret['official_address'] = format_address(address)
        if proofing_state:
            # Just update address if the user already has started the proofing flow
            proofing_state.proofing_letter.address = address
            db.letter_proofing_statedb.save(proofing_state)
        else:
            # Create a LetterNinProofingUser in proofingdb
            proofing_state = create_proofing_state(user.user_id, nin)
            proofing_state.proofing_letter.address = address
            db.letter_proofing_statedb.save(proofing_state)
            app.logger.info('Created proofing state for user {!r}'.format(user))
        return jsonify(ret)
    else:
        app.logger.error('ApiException {!r}'.format(form.errors))
        raise ApiException({'errors': form.errors}, status_code=400)


@app.route('/send-letter', methods=['POST'])
def send_letter():
    form = AcceptAddressForm()
    if form.validate_on_submit():
        user = authenticate(form)
        app.logger.info('Sending letter for user {!r}'.format(user))
        if not form.accepted_address.data:
            app.logger.info('User {!r} declined address'.format(user))
            raise ApiException({'success': False, 'reason': 'User declined address'}, status_code=200)
        proofing_state = db.letter_proofing_statedb.get_state_by_user_id(user.user_id)
        if proofing_state.proofing_letter.is_sent:
            app.logger.info('User {!r} has already sent a letter'.format(user))
            raise ApiException({'success': False, 'reason': 'Letter already sent'}, status_code=200)

        # User accepted the official address and data saved in db checks out
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
        raise ApiException({'errors': form.errors}, status_code=400)


@app.route('/verify-code', methods=['POST'])
def verify_code():
    form = VerifyCodeForm()
    if form.validate_on_submit():
        user = authenticate(form)
        app.logger.info('Verifying code for user {!r}'.format(user))
        proofing_state = db.letter_proofing_statedb.get_state_by_user_id(user.user_id)
        if not form.verification_code.data == proofing_state.nin.verification_code:
            app.logger.error('Verification code for user {!r} does not match'.format(user))
            raise ApiException({'success': False, 'reason': 'Verification code does not match'}, status_code=200)
        proofing_state.nin.is_verified = True
        proofing_state.nin.verified_by = 'eduid-idproofing-letter'
        proofing_state.nin.verified_ts = True
        # TODO: Create a JWT and send required data to a Proofing Assertion Consumer
        app.logger.info('Verified code for user {!r}'.format(user))
        # Remove proofing user
        db.letter_proofing_statedb.remove_document({'user_id': proofing_state.user_id})
        nin = proofing_state.nin.to_dict()
        ret = {'success': True, 'data': nin}
        return jsonify(ret)
    else:
        app.logger.error('ApiException {!r}'.format(form.errors))
        raise ApiException({'errors': form.errors}, status_code=400)


