# -*- coding: utf-8 -*-

from __future__ import absolute_import

from flask import url_for
from flask_wtf.csrf import generate_csrf

from datetime import datetime, timedelta

from eduid_userdb.proofing import LetterNinProofingUser

from idproofing_letter import app, proofingdb
from idproofing_letter.celery_mock import get_formatted_address
from idproofing_letter.forms import NinForm, AcceptAddressForm, VerifyCodeForm
from idproofing_letter.utils import get_short_hash

__author__ = 'lundberg'

def check_user_status(user):
    """
    :param user:  authenticated user
    :type user:  LetterNinProofingUser
    :return: response
    :rtype: dict
    """
    ret = dict()
    if not user.proofing_letter.is_sent:
        # Show user official address
        ret.update({
            'endpoint': url_for('send_letter', _external=True),
            'csrf': generate_csrf(),
            'expected_fields': AcceptAddressForm()._fields.keys()  # Do we want expected_fields?
        })
        # TODO: Lookup official address via Navet and return address for confirmation
        ret['official_address'] = get_formatted_address(user.nin.number)
    elif user.proofing_letter.is_sent:
        # Check how long ago the letter was sent
        now = datetime.utcnow()
        sent_dt = user.proofing_letter.sent_ts
        if now - sent_dt < timedelta(hours=app.config['LETTER_WAIT_TIME_HOURS']):
            # The user have to wait for the letter to arrive
            ret.update({
                'endpoint': url_for('verify_code', _external=True),
                'csrf': generate_csrf(),
                'expected_fields': VerifyCodeForm()._fields.keys()  # Do we want expected_fields?
                #'wait_time'   # The user has to wait this many days before sending another letter
            })
        else:
            # If the letter haven't reached the user within the allotted time
            # remove the previous proofing object and restart the proofing flow
            proofingdb.remove(user.to_dict())
            ret.update({
                'endpoint': url_for('get-address', _external=True),
                'expected_fields': NinForm()._fields.keys(),  # Do we want expected_fields?
                'csrf': generate_csrf()
            })
    return ret


def create_proofing_user(user_id, nin):
    proofing_user = LetterNinProofingUser({
        'user_id': user_id,
        'nin': {
            'number': nin,
            'created_by': 'eduid-idproofing-letter',
            'created_ts': True,
            'verified': False,
            'verification_code': get_short_hash()
        }
    })
    return proofing_user
