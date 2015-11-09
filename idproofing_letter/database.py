# -*- coding: utf-8 -*-

from __future__ import absolute_import

from flask import current_app
from eduid_userdb.userdb import UserDB
from eduid_userdb.proofing.proofingdb import LetterProofingStateDB

__author__ = 'lundberg'

def get_userdb():
    """
    :return: UserDB object
    :rtype: UserDB
    """
    from idproofing_letter import app
    db = getattr(current_app, '_userdb', None)
    if db is None:
        db = current_app._userdb = UserDB(app.config['USERDB_MONGO_URI'], 'eduid_am')
        app.logger.info('userdb initialized')
    return db


def get_proofingdb():
    """
    :return: LetterNinProofingUserDB object
    :rtype: LetterNinProofingUserDB
    """
    from idproofing_letter import app
    db = getattr(current_app, '_proofingdb', None)
    if db is None:
        db = current_app._proofingdb = LetterProofingStateDB(app.config['IDPROOFING_MONGO_URI'],
                                                             'eduid_idproofing_letter')
        app.logger.info('proofingdb initialized')
    return db







