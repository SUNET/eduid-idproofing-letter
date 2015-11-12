# -*- coding: utf-8 -*-

from __future__ import absolute_import

from flask import url_for
from flask_wtf.csrf import generate_csrf

from datetime import datetime, timedelta

from eduid_userdb.proofing import LetterProofingState

from idproofing_letter import app, proofingdb
from idproofing_letter.celery import format_address
from idproofing_letter.forms import NinForm, AcceptAddressForm, VerifyCodeForm
from idproofing_letter.utils import get_short_hash

__author__ = 'lundberg'

def check_state(state):
    """
    :param state:  Users proofing state
    :type state:  LetterProofingState
    :return: response
    :rtype: dict
    """
    ret = dict()
    if not state.proofing_letter.is_sent:
        # Show user official address
        ret.update({
            'endpoint': url_for('send_letter', _external=True),
            'csrf': generate_csrf(),
            'expected_fields': AcceptAddressForm()._fields.keys()  # Do we want expected_fields?
        })
        # XXX: Should we lookup the address again?
        ret['official_address'] = format_address(state.proofing_letter.address)
    elif state.proofing_letter.is_sent:
        # Check how long ago the letter was sent
        sent_dt = state.proofing_letter.sent_ts
        now = datetime.now(sent_dt.tzinfo)  # Use tz_info from timezone aware mongodb datetime
        max_wait = timedelta(hours=app.config['LETTER_WAIT_TIME_HOURS'])

        time_since_sent = now - sent_dt
        if time_since_sent < max_wait:
            # The user has to wait for the letter to arrive
            ret.update({
                'endpoint': url_for('verify_code', _external=True),
                'csrf': generate_csrf(),
                'wait_time': '{!s}'.format(max_wait - time_since_sent),
                'expected_fields': VerifyCodeForm()._fields.keys(),  # Do we want expected_fields?
            })
        else:
            # If the letter haven't reached the user within the allotted time
            # remove the previous proofing object and restart the proofing flow
            proofingdb.remove_document({'user_id': state.user_id})
            app.logger.info('Removed {!s}'.format(state))
            ret.update({
                'endpoint': url_for('get_address', _external=True),
                'expected_fields': NinForm()._fields.keys(),  # Do we want expected_fields?
                'csrf': generate_csrf()
            })
    return ret


def create_proofing_state(user_id, nin):
    proofing_state = LetterProofingState({
        'user_id': user_id,
        'nin': {
            'number': nin,
            'created_by': 'eduid-idproofing-letter',
            'created_ts': True,
            'verified': False,
            'verification_code': get_short_hash()
        }
    })
    return proofing_state
