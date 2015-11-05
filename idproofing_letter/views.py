# -*- coding: utf-8 -*-

from __future__ import absolute_import

from flask import g, request, render_template, jsonify, url_for
from flask_wtf.csrf import generate_csrf

from datetime import datetime, timedelta

from eduid_userdb.proofing import LetterNinProofingUserDB, LetterNinProofingUser

from idproofing_letter import app, csrf, userdb, proofingdb
from idproofing_letter.exceptions import ApiException
from idproofing_letter.forms import NinForm, AcceptAddressForm, VerifyCodeForm
from idproofing_letter.utils import get_short_hash

# Dev mocks
from idproofing_letter import celery_mock

__author__ = 'lundberg'


@app.route('/')
def index():
    # A view for developing, should not be exposed in production
    return render_template('index.html', message='eduid-proofing-letter', form1=NinForm(), form2=AcceptAddressForm())


@app.route('/get-address', methods=['GET', 'POST'])
def get_address():
    # TODO: Authenticate user
    user = userdb.get_user_by_eppn(app.config['DEV_EPPN'])
    proofing_user = proofingdb.get_user_by_id(user.user_id, raise_on_missing=False)
    form = NinForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            if proofing_user:
                pass  # TODO: Check if user status
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
                'nin': {
                    'number': form.nin.data,
                    'created_by': 'eduid-idproofing-letter',
                    'created_ts': True,
                    'verified': False,
                    'verification_code': get_short_hash()
                }
            })
            proofingdb.save(proofing_user, user_id_attr='user_id')
            return jsonify(ret)
        raise ApiException({'errors': form.errors}, status_code=400)
    else:  # GET
        if proofing_user:
            if not proofing_user.proofing_letter.is_sent:
                ret = dict({
                    'endpoint': url_for('send_letter', _external=True),
                    'csrf': generate_csrf(),
                    'expected_fields': AcceptAddressForm()._fields.keys()  # Do we want expected_fields?
                })
                # TODO: Lookup official address via Navet and return address for confirmation
                ret['official_address'] = celery_mock.get_formatted_address(form.nin.data)
                return jsonify(ret)
            else:
                now = datetime.utcnow()
                sent_dt = proofing_user.proofing_letter.sent_ts
                if now - sent_dt < timedelta(weeks=app.config['LETTER_WAIT_TIME_HOURS']):
                    ret = dict({
                        'endpoint': url_for('verify_code', _external=True),
                        'csrf': generate_csrf(),
                        'expected_fields': VerifyCodeForm()._fields.keys()  # Do we want expected_fields?
                    })
                    return jsonify(ret)
                else:
                    # If the letter haven't reached the user within the allotted time
                    # remove the previous proofing object and create a new one
                    proofingdb.remove(proofing_user.to_dict())

        ret = {
            'endpoint': request.url,
            'expected_fields': form._fields.keys(),  # Do we want expected_fields?
            'csrf': generate_csrf()
        }

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


