# -*- coding: utf-8 -*-

from __future__ import absolute_import

from idproofing_letter import app
from eduid_msg.celery import celery
from eduid_msg.tasks import get_postal_address as _get_postal_address

__author__ = 'lundberg'


celery.conf.update(app.config['CELERY_CONFIG'])


def get_postal_address(nin):
    """
    :param nin: Swedish national identity number
    :type nin: string
    :return: Official name and postal address
    :rtype: OrderedDict|None

        The expected address format is:

            OrderedDict([
                (u'Name', OrderedDict([
                    (u'GivenNameMarking', u'20'),
                    (u'GivenName', u'personal name'),
                    (u'SurName', u'thesurname')
                ])),
                (u'OfficialAddress', OrderedDict([
                    (u'Address2', u'StreetName 103'),
                    (u'PostalCode', u'74141'),
                    (u'City', u'STOCKHOLM')
                ]))
            ])
    """

    rtask = _get_postal_address.apply_async(args=[nin])
    try:
        rtask.wait()
        if rtask.successful():
            return rtask.get()
    except Exception as e:
        app.logger.error('Celery task failed: {!r}'.format(e))
        raise e
    return None


def format_address(address):
    """
    :param address: official address
    :type address: OrderedDict
    :return: formatted address
    :rtype: list
    """
    # TODO: Take GivenNameMarking in to account
    lines = list()
    lines.append(u'{GivenName} {SurName}'.format(**address.get('Name')))
    # TODO: Take eventual CareOf and Address1(?) in to account
    lines.append(u'{}'.format(address.get('OfficialAddress').get('Address2')))
    lines.append(u'{PostalCode} {City}'.format(**address.get('OfficialAddress')))
    return lines


# from collections import OrderedDict
# def get_postal_address(nin):
#         result = OrderedDict([
#             (u'Name', OrderedDict([
#                 (u'GivenNameMarking', u'20'), (u'GivenName', u'Testaren Test'),
#                 (u'SurName', u'Testsson')])),
#             (u'OfficialAddress', OrderedDict([(u'Address2', u'\xd6RGATAN 79 LGH 10'),
#                                               (u'PostalCode', u'12345'),
#                                               (u'City', u'LANDET')]))
#         ])
#         return result