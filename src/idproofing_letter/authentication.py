# -*- coding: utf-8 -*-

from __future__ import absolute_import

from flask import current_app
from eduid_userdb.exceptions import UserDoesNotExist, MultipleUsersReturned
from eduid_common.api.exceptions import ApiException

__author__ = 'lundberg'


# TODO: Not for production use
def authenticate(data):
    """
    :param data:
    :type data: dict
    :return: authenticated users of False
    :rtype: eduid_userdb.user.User
    """
    eppn = data.get('eppn')
    current_app.logger.info('Trying to authenticate user {!s}'.format(eppn))

    if not eppn:
        current_app.logger.error('No eppn provided. No user to authenticate.')

    # Get user from central database
    try:
        user = current_app.central_userdb.get_user_by_eppn(eppn, raise_on_missing=True)
    except (UserDoesNotExist, MultipleUsersReturned) as e:
        current_app.logger.error('Could not find user or found multiple users in central database.')
        current_app.logger.error(e)
        raise ApiException('Not authorized', status_code=401)

    return user

