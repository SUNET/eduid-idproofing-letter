# -*- coding: utf-8 -*-

from __future__ import absolute_import

from copy import deepcopy

from flask import request

from eduid_userdb.testing import MongoTestCase
from idproofing_letter import app, db
from idproofing_letter.authentication import authenticate

__author__ = 'lundberg'


SETTINGS = {
    'TESTING': True,
    'DEV_EPPN': 'babba-labba',
}


class AppTests(MongoTestCase):
    """Base TestCase for those tests that need a full environment setup"""

    def setUp(self):
        super(AppTests, self).setUp(None, None, userdb_use_old_format=True)

        _settings = deepcopy(SETTINGS)
        _settings.update({
            'MONGO_URI': self.tmp_db.get_uri(),
            })
        self.settings.update(_settings)

        app.config.update(self.settings)

        self.testapp = app.test_client()

    def tearDown(self):
        super(AppTests, self).tearDown()
        with app.app_context():
            db.letter_proofing_statedb._drop_whole_collection()
            db.userdb._drop_whole_collection()

    def test_authenticate(self):
        with app.test_request_context():
            self.testapp.get('/get-state')
            user = authenticate(request)
            self.assertEqual(user.eppn, SETTINGS['DEV_EPPN'])
