# -*- coding: utf-8 -*-

from __future__ import absolute_import

from flask import g
from eduid_userdb.userdb import UserDB
from eduid_userdb.proofing.userdb import LetterNinProofingUserDB

__author__ = 'lundberg'


def get_userdb():
    """
    :return: UserDB object
    :rtype: UserDB
    """
    import runserver
    db = getattr(g, '_userdb', None)
    if db is None:
        db = g._userdb = UserDB(runserver.app.config['USERDB_MONGO_URI'], 'eduid_am')
        runserver.app.logger.warning('userdb initialized')
    return db


def get_proofingdb():
    """
    :return: LetterNinProofingUserDB object
    :rtype: LetterNinProofingUserDB
    """
    import runserver
    db = getattr(g, '_proofingdb', None)
    if db is None:
        db = g._proofingdb = LetterNinProofingUserDB(runserver.app.config['IDPROOFING_MONGO_URI'],
                                                     'eduid_idproofing_letter')
        runserver.app.logger.warning('proofingdb initialized')
    return db







