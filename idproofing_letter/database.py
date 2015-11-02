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
    import idproofing_letter_app
    db = getattr(g, '_userdb', None)
    if db is None:
        db = g._userdb = UserDB(idproofing_letter_app.app.config['USERDB_MONGO_URI'], 'eduid_am')
        idproofing_letter_app.app.logger.warning('userdb initialized')
    return db


def get_proofingdb():
    """
    :return: LetterNinProofingUserDB object
    :rtype: LetterNinProofingUserDB
    """
    import idproofing_letter_app
    db = getattr(g, '_proofingdb', None)
    if db is None:
        db = g._proofingdb = LetterNinProofingUserDB(idproofing_letter_app.app.config['IDPROOFING_MONGO_URI'],
                                                     'eduid_idproofing_letter')
        idproofing_letter_app.app.logger.warning('proofingdb initialized')
    return db







