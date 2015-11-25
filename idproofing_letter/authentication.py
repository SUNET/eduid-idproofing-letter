# -*- coding: utf-8 -*-

from __future__ import absolute_import

from eduid_userdb.exceptions import UserDoesNotExist, MultipleUsersReturned

from idproofing_letter import app, db
from idproofing_letter.exceptions import ApiException

__author__ = 'lundberg'


# TODO: Get user auth info from something else than a cookie
# TODO: Maybe we should use sessions so we don't have to re-auth the user
# TODO: for each call.
def authenticate(request):
    """
    :param request: incoming request
    :type request: flask.request
    :return: authenticated users of False
    :rtype: eduid_userdb.user.User
    """
    eppn = request.cookies.get('eppn', None)
    # TODO: Remove dev workaround
    if not eppn:
        eppn = app.config['DEV_EPPN']

    # Get user from central database
    try:
        user = db.userdb.get_user_by_eppn(eppn, raise_on_missing=True)
    except (UserDoesNotExist, MultipleUsersReturned) as e:
        app.logger.error('Could not find user or found multiple users in central database.')
        app.logger.error(e)
        raise ApiException('Not authorized', status_code=401)

    return user

