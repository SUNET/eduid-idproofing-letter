# -*- coding: utf-8 -*-

from __future__ import absolute_import

from copy import deepcopy
from os import devnull
import json
from datetime import datetime
from collections import OrderedDict
from mock import patch
from bson import ObjectId

from flask import request
from eduid_userdb.testing import MongoTestCase
from eduid_userdb import UserDB
from eduid_userdb.proofing import LetterProofingStateDB
from idproofing_letter.app import init_idproofing_letter_app
from idproofing_letter.schemas import EppnRequestSchema
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
        self.app = init_idproofing_letter_app('testing', _settings)

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
        self._json = 'application/json'

        self.client = self.app.test_client()

    def tearDown(self):
        super(AppTests, self).tearDown()
        with self.app.app_context():
            self.app.proofing_statedb._drop_whole_collection()
            self.app.central_userdb._drop_whole_collection()

    # Helper methods
    def get_state(self, eppn):
        data = {'eppn': eppn}
        response = self.client.post('/get-state', data=json.dumps(data), content_type=self._json)
        self.assertEqual(response.status_code, 200)
        return json.loads(response.data)

    @patch('idproofing_letter.views.get_postal_address')
    def send_letter(self, eppn, nin, mock_get_postal_address):
        mock_get_postal_address.return_value = self.mock_address
        data = {'eppn': eppn, 'nin': nin}
        response = self.client.post('/send-letter', data=json.dumps(data), content_type=self._json)
        self.assertEqual(response.status_code, 200)
        return json.loads(response.data)

    def verify_code(self, eppn, code):
        data = {'eppn': eppn, 'verification_code': code}
        response = self.client.post('/verify-code', data=json.dumps(data), content_type=self._json)
        self.assertEqual(response.status_code, 200)
        return json.loads(response.data)
    # End helper methods

    def test_authenticate(self):
        data = {'eppn': self.test_user_eppn}
        with self.app.test_request_context('/get-state', method='POST', data=json.dumps(data), content_type=self._json):
            schema, errors = EppnRequestSchema().load(request.get_json())
            if not errors:
                user = authenticate(schema)
                self.assertEqual(user.eppn, self.test_user_eppn)

    def test_bad_input_get_status(self):
        data = {'not_eppn': 'dummy'}
        response = self.client.post('/get-state', data=json.dumps(data), content_type=self._json)
        self.assertEqual(response.status_code, 422)
        response_data = json.loads(response.data)
        self.assertIn('eppn', response_data)

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
        with self.app.test_request_context():
            with self.app.app_context():
                proofing_state = self.app.proofing_statedb.get_state_by_eppn(self.test_user_eppn, raise_on_missing=False)
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
        with self.app.test_request_context():
            user = self.app.central_userdb.get_user_by_eppn(self.test_user_eppn, raise_on_missing=True)
            proofing_state = self.app.proofing_statedb.get_state_by_eppn(user.eppn, raise_on_missing=False)
        json_data = self.verify_code(self.test_user_eppn, proofing_state.nin.verification_code)
        self.assertTrue(json_data['success'])
        proofing_data = json_data.get('data', None)
        self.assertTrue(proofing_data.get('verified', False))

    def test_expire_proofing_state(self):
        self.send_letter(self.test_user_eppn, self.test_user_nin)
        json_data = self.get_state(self.test_user_eppn)
        self.assertIn('letter_sent', json_data)
        self.app.config.update({'LETTER_WAIT_TIME_HOURS': -1})
        json_data = self.get_state(self.test_user_eppn)
        self.assertTrue(json_data['letter_expired'])
        self.assertNotIn('letter_sent', json_data)

    def test_deprecated_proofing_state(self):
        deprecated_data = {
            'user_id': ObjectId('012345678901234567890123'),
            'nin': {
                'created_by': 'eduid-userdb.tests',
                'created_ts': datetime(2015, 11, 9, 12, 53, 9, 708761),
                'number': '200102034567',
                'verification_code': 'abc123',
                'verified': False
            },
            'proofing_letter': {
                'is_sent': False,
                'sent_ts': None,
                'transaction_id': None,
                'address': self.mock_address
            }
        }
        with self.app.app_context():
            self.app.proofing_statedb._coll.insert(deprecated_data)
            state = self.app.proofing_statedb.get_state_by_user_id('012345678901234567890123', self.test_user_eppn)
        self.assertIsNotNone(state)
        state_dict = state.to_dict()
        self.assertItemsEqual(state_dict.keys(), ['_id', 'eduPersonPrincipalName', 'nin', 'proofing_letter',
                                                  'modified_ts'])
        self.assertItemsEqual(state_dict['nin'].keys(), ['created_by', 'created_ts', 'number', 'verification_code',
                                                         'verified'])
        self.assertItemsEqual(state_dict['proofing_letter'].keys(), ['is_sent', 'sent_ts', 'transaction_id',
                                                                     'address'])


