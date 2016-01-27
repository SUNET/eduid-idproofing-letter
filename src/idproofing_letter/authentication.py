# -*- coding: utf-8 -*-

from __future__ import absolute_import

from eduid_userdb.exceptions import UserDoesNotExist, MultipleUsersReturned

from idproofing_letter import app, db
from eduid_common.api.exceptions import ApiException

__author__ = 'lundberg'


# TODO: Get user auth info from something else than a cookie
# TODO: Maybe we should use sessions so we don't have to re-auth the user
# TODO: for each call.
def authenticate(form):
    """
    :param form:
    :type form: flask_wtf.form.Form
    :return: authenticated users of False
    :rtype: eduid_userdb.user.User
    """
    eppn = form.eppn.data
    app.logger.info('Trying to authenticate user {!s}'.format(eppn))

    if not eppn:
        app.logger.error('No eppn provided. No user to authenticate.')

    # Get user from central database
    try:
        user = db.userdb.get_user_by_eppn(eppn, raise_on_missing=True)
    except (UserDoesNotExist, MultipleUsersReturned) as e:
        app.logger.error('Could not find user or found multiple users in central database.')
        app.logger.error(e)
        raise ApiException('Not authorized', status_code=401)

    return user

