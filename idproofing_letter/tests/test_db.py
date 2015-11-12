# -*- coding: utf-8 -*-

from __future__ import absolute_import

from copy import deepcopy

from flask import request

from eduid_userdb.testing import MongoTestCase
from idproofing_letter import app, userdb, proofingdb
from idproofing_letter.authentication import authenticate

__author__ = 'lundberg'


SETTINGS = {
    'TESTING': True,
    'DEV_EPPN': 'babba-labba',
}


class DbTests(MongoTestCase):
    """Base TestCase for those tests that need a full environment setup"""

    def setUp(self):
        super(DbTests, self).setUp(None, None, userdb_use_old_format=True)

        _settings = deepcopy(SETTINGS)
        _settings.update({
            'IDPROOFING_MONGO_URI': self.tmp_db.get_uri('eduid_idproofing_letter_test'),
            'USERDB_MONGO_URI': self.tmp_db.get_uri('eduid_am'),
            })
        self.settings.update(_settings)

        app.config.update(self.settings)

        self.testapp = app.test_client()

    def tearDown(self):
        super(DbTests, self).tearDown()
        with app.app_context():
            proofingdb._drop_whole_collection()
            userdb._drop_whole_collection()

    def test_authenticate(self):
#        with app.app_context():
        self.testapp
        user = authenticate(request)
        self.assertEqual(user.eppn, 'babba-labba')
