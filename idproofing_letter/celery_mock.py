# -*- coding: utf-8 -*-

from collections import OrderedDict

__author__ = 'lundberg'

def get_postal_address(nin):
        result = OrderedDict([
            (u'Name', OrderedDict([
                (u'GivenNameMarking', u'20'), (u'GivenName', u'Testaren Test'),
                (u'SurName', u'Testsson')])),
            (u'OfficialAddress', OrderedDict([(u'Address2', u'\xd6RGATAN 79 LGH 10'),
                                              (u'PostalCode', u'12345'),
                                              (u'City', u'LANDET')]))
        ])
        return result

def get_formatted_address(nin):
    postal_address = get_postal_address(nin)
    # TODO: Take GivenNameMarking in to account
    lines = list()
    lines.append(u'{GivenName} {SurName}'.format(**postal_address.get('Name')))
    # TODO: Take eventual CareOf and Address1(?) in to account
    lines.append(u'{}'.format(postal_address.get('OfficialAddress').get('Address2')))
    lines.append(u'{PostalCode} {City}'.format(**postal_address.get('OfficialAddress')))
    return lines
