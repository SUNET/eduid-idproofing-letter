# -*- coding: utf-8 -*-

import re
from flask_wtf import Form
from wtforms import StringField, BooleanField
from wtforms.validators import regexp, required

__author__ = 'lundberg'

nin_re = re.compile(r'^(18|19|20)\d{2}(0[1-9]|1[0-2])\d{2}\d{4}$')


class NinForm(Form):

    eppn = StringField(u'eppn', validators=[required()])  # Dev
    nin = StringField(u'nin', validators=[regexp(nin_re, message="nin needs to be formatted as 18|19|20yymmddxxxx")])

class AcceptAddressForm(Form):

    eppn = StringField(u'eppn', validators=[required()])  # Dev
    accepted_address = BooleanField(u'accepted_address', validators=[required()])

