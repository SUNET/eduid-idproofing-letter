# -*- coding: utf-8 -*-

from __future__ import absolute_import

from copy import deepcopy
from os import devnull
import json
from datetime import datetime
from collections import OrderedDict
from mock import patch

from eduid_userdb.testing import MongoTestCase
from idproofing_letter import app, db
from idproofing_letter.forms import GetState
from idproofing_letter.authentication import authenticate

__author__ = 'lundberg'


SETTINGS = {
    'TESTING': True,
    'SECRET_KEY': 'testing',
    'EKOPOST_DEBUG_PDF': devnull,
    'LETTER_WAIT_TIME_HOURS': 336
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

        self.test_user_eppn = 'babba-labba'
        self.test_user_nin = '200001023456'
        self.mock_address = OrderedDict([
            (u'Name', OrderedDict([
                (u'GivenNameMarking', u'20'), (u'GivenName', u'Testaren Test'),
                (u'Surname', u'Testsson')])),
            (u'OfficialAddress', OrderedDict([(u'Address2', u'\xd6RGATAN 79 LGH 10'),
                                              (u'PostalCode', u'12345'),
                                              (u'City', u'LANDET')]))
        ])

        self.testapp = app.test_client()

    def tearDown(self):
        super(AppTests, self).tearDown()
        with app.app_context():
            db.letter_proofing_statedb._drop_whole_collection()
            db.userdb._drop_whole_collection()

    # Helper methods
    def get_state(self, eppn):
        data = {'eppn': eppn}
        response = self.testapp.post('/get-state', data=data)
        self.assertEqual(response.status_code, 200)
        return json.loads(response.data)

    @patch('idproofing_letter.views.get_postal_address')
    def send_letter(self, eppn, nin, mock_get_postal_address):
        mock_get_postal_address.return_value = self.mock_address
        data = {'eppn': eppn, 'nin': nin}
        response = self.testapp.post('/send-letter', data=data)
        self.assertEqual(response.status_code, 200)
        return json.loads(response.data)

    def verify_code(self, eppn, code):
        data = {'eppn': eppn, 'verification_code': code}
        response = self.testapp.post('/verify-code', data=data)
        self.assertEqual(response.status_code, 200)
        return json.loads(response.data)

    # End helper methods

    def test_authenticate(self):
        with app.test_request_context():
            self.testapp.get('/get-state')
            form = GetState()
            if form.validate_on_submit():
                user = authenticate(form)
                self.assertEqual(user.eppn, self.test_user_eppn)

    def test_letter_not_sent_status(self):
        json_data = self.get_state(self.test_user_eppn)
        self.assertNotIn('letter_sent', json_data)

    def test_send_letter(self):
        json_data = self.send_letter(self.test_user_eppn, self.test_user_nin)
        expires = json_data['letter_expires']
        expires = datetime.utcfromtimestamp(int(expires))
        self.assertIsInstance(expires, datetime)
        expires = expires.strftime('%Y-%m-%d')
        self.assertIsInstance(expires, basestring)

    def test_letter_sent_status(self):
        self.send_letter(self.test_user_eppn, self.test_user_nin)
        json_data = self.get_state(self.test_user_eppn)
        self.assertIn('letter_sent', json_data)
        expires = datetime.utcfromtimestamp(int(json_data['letter_expires']))
        self.assertIsInstance(expires, datetime)
        expires = expires.strftime('%Y-%m-%d')
        self.assertIsInstance(expires, basestring)

    def test_verify_letter_code(self):
        self.send_letter(self.test_user_eppn, self.test_user_nin)
        with app.test_request_context():
            user = db.userdb.get_user_by_eppn(self.test_user_eppn, raise_on_missing=True)
            # TODO: Need to change get_state_by_user_id to get_state_by_eppn
            proofing_state = db.letter_proofing_statedb.get_state_by_user_id(user.user_id, raise_on_missing=False)
        json_data = self.verify_code(self.test_user_eppn, proofing_state.nin.verification_code)
        self.assertTrue(json_data['success'])
        proofing_data = json_data.get('data', None)
        self.assertTrue(proofing_data.get('verified', False))
        created_ts = datetime.utcfromtimestamp(int(proofing_data['created_ts']))
        self.assertIsInstance(created_ts, datetime)
        verified_ts = datetime.utcfromtimestamp(int(proofing_data['verified_ts']))
        self.assertIsInstance(verified_ts, datetime)

    def test_verify_letter_code_fail(self):
        self.send_letter(self.test_user_eppn, self.test_user_nin)
        json_data = self.verify_code(self.test_user_eppn, 'wrong code')
        self.assertFalse(json_data['success'])

    def test_proofing_flow(self):
        self.get_state(self.test_user_eppn)
        self.send_letter(self.test_user_eppn, self.test_user_nin)
        self.get_state(self.test_user_eppn)
        with app.test_request_context():
            user = db.userdb.get_user_by_eppn(self.test_user_eppn, raise_on_missing=True)
            # TODO: Need to change get_state_by_user_id to get_state_by_eppn
            proofing_state = db.letter_proofing_statedb.get_state_by_user_id(user.user_id, raise_on_missing=False)
        json_data = self.verify_code(self.test_user_eppn, proofing_state.nin.verification_code)
        self.assertTrue(json_data['success'])
        proofing_data = json_data.get('data', None)
        self.assertTrue(proofing_data.get('verified', False))

    def test_expire_proofing_state(self):
        self.send_letter(self.test_user_eppn, self.test_user_nin)
        json_data = self.get_state(self.test_user_eppn)
        self.assertIn('letter_sent', json_data)
        app.config.update({'LETTER_WAIT_TIME_HOURS': -1})
        self.testapp = app.test_client()
        json_data = self.get_state(self.test_user_eppn)
        self.assertNotIn('letter_sent', json_data)
