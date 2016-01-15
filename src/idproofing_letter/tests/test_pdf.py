# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest
from collections import OrderedDict
from idproofing_letter.pdf import format_address
from idproofing_letter.exceptions import ApiException

# We need to add Navet responses that we fail to handle

__author__ = 'lundberg'


class FormatAddressTest(unittest.TestCase):

    def test_successful_format(self):

        navet_responses = [
            OrderedDict([
                (u'Name', OrderedDict([
                    (u'GivenNameMarking', u'20'), (u'GivenName', u'Testaren Test'),
                    (u'Surname', u'Testsson')])),
                (u'OfficialAddress', OrderedDict([(u'Address2', u'\xd6RGATAN 79 LGH 10'),
                                                  (u'PostalCode', u'12345'),
                                                  (u'City', u'LANDET')]))
            ]),
            OrderedDict([
                (u'Name', OrderedDict([
                    (u'GivenNameMarking', u'20'), (u'GivenName', u'Testaren Test'),
                    (u'MiddleName', u'Tester'), (u'Surname', u'Testsson')])),
                (u'OfficialAddress', OrderedDict([(u'Address2', u'\xd6RGATAN 79 LGH 10'),
                                                  (u'PostalCode', u'12345'),
                                                  (u'City', u'LANDET')]))
            ])
        ]
        for response in navet_responses:
            name, address, postal_code = format_address(response)
            self.assertIsNotNone(name)
            self.assertIsNotNone(address)
            self.assertIsNotNone(postal_code)

    def test_failing_format(self):

        failing_navet_responses = [
            OrderedDict([
                (u'OfficialAddress', OrderedDict([(u'Address2', u'\xd6RGATAN 79 LGH 10'),
                                                  (u'PostalCode', u'12345'),
                                                  (u'City', u'LANDET')]))
            ]),
            OrderedDict([
                (u'Name', OrderedDict([
                    (u'GivenNameMarking', u'20'), (u'GivenName', u'Testaren Test'),
                    (u'Surname', u'Testsson')])),
            ]),
            OrderedDict([
                (u'Name', OrderedDict([
                    (u'GivenNameMarking', u'20'), (u'Surname', u'Testsson')])),
                (u'OfficialAddress', OrderedDict([(u'Address2', u'\xd6RGATAN 79 LGH 10'),
                                                  (u'PostalCode', u'12345'),
                                                  (u'City', u'LANDET')]))
            ]),
            OrderedDict([
                (u'Name', OrderedDict([
                    (u'GivenNameMarking', u'20'), (u'Surname', u'Testsson')])),
                (u'OfficialAddress', OrderedDict([(u'Address2', u'\xd6RGATAN 79 LGH 10'),
                                                  (u'City', u'LANDET')]))
            ])
        ]
        for response in failing_navet_responses:
            self.assertRaises(ApiException, format_address, response)

