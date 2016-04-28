# -*- coding: utf-8 -*-

from __future__ import absolute_import

from flask import current_app, url_for
from datetime import datetime, timedelta

from eduid_userdb.proofing import LetterProofingState
from eduid_common.api.utils import get_short_hash
from idproofing_letter.schemas import SendLetterRequestSchema, VerifyCodeRequestSchema

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
        # User needs to accept sending a letter
        ret.update({
            'endpoint': url_for('idproofing_letter.send_letter', _external=True),
            'expected_fields': SendLetterRequestSchema().fields.keys()  # Do we want expected_fields?
        })
    elif state.proofing_letter.is_sent:
        # Check how long ago the letter was sent
        sent_dt = state.proofing_letter.sent_ts
        now = datetime.now(sent_dt.tzinfo)  # Use tz_info from timezone aware mongodb datetime
        max_wait = timedelta(hours=current_app.config['LETTER_WAIT_TIME_HOURS'])

        time_since_sent = now - sent_dt
        if time_since_sent < max_wait:
            # The user has to wait for the letter to arrive
            ret.update({
                'endpoint': url_for('idproofing_letter.verify_code', _external=True),
                'letter_sent': sent_dt,
                'letter_expires': sent_dt + max_wait,
                'expected_fields': VerifyCodeRequestSchema().fields.keys(),  # Do we want expected_fields?
            })
        else:
            # If the letter haven't reached the user within the allotted time
            # remove the previous proofing object and restart the proofing flow
            current_app.proofing_statedb.remove_document({'eduPersonPrincipalName': state.eppn})
            current_app.logger.info('Removed {!s}'.format(state))
            ret.update({
                'endpoint': url_for('idproofing_letter.send_letter', _external=True),
                'letter_expired': True,
                'expected_fields': SendLetterRequestSchema().fields.keys(),  # Do we want expected_fields?
            })
    return ret


def create_proofing_state(eppn, nin):
    proofing_state = LetterProofingState({
        'eduPersonPrincipalName': eppn,
        'nin': {
            'number': nin,
            'created_by': 'eduid-idproofing-letter',
            'created_ts': True,
            'verified': False,
            'verification_code': get_short_hash()
        }
    })
    return proofing_state
