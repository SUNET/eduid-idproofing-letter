# -*- coding: utf-8 -*-

import re
from marshmallow import Schema, fields, ValidationError, pre_dump
from idproofing_letter import app

__author__ = 'lundberg'

nin_re = re.compile(r'^(18|19|20)\d{2}(0[1-9]|1[0-2])\d{2}\d{4}$')


# Common
class ProofingDataSchema(Schema):

    class Meta:
        strict = True

    number = fields.String(required=True)
    created_by = fields.String(required=True)
    created_ts = fields.Integer(required=True)
    verified = fields.Boolean(required=True)
    verified_by = fields.String(required=True)
    verified_ts = fields.Integer(required=True)
    verification_code = fields.String(required=True)
    official_address = fields.Dict(required=True)
    transaction_id = fields.String(required=True)

    # XXX: For maintaining UNIX TS for datetimes
    @pre_dump
    def eduid_datetime_encoder(self, in_data):
        for key in ['created_ts', 'verified_ts']:
            dt = in_data.get(key)
            if dt:
                in_data[key] = app.json_encoder().default(dt)
        return in_data


def validate_nin(nin):
    if nin_re.match(nin):
        return True
    raise ValidationError('nin needs to be formatted as 18|19|20yymmddxxxx')
# End common


# Input validation
class EppnRequestSchema(Schema):

    class Meta:
        strict = True

    eppn = fields.String(required=True)


class SendLetterRequestSchema(EppnRequestSchema):

    nin = fields.String(required=True, validate=validate_nin)


class VerifyCodeRequestSchema(EppnRequestSchema):

    verification_code = fields.String(required=True)
# End input validation


# Output validation
class BaseResponseSchema(Schema):

    class Meta:
        strict = True

    endpoint = fields.Url(required=True)
    expected_fields = fields.List(fields.String, required=True)


class GetStateResponseSchema(BaseResponseSchema):

    letter_sent = fields.Boolean()
    letter_expires = fields.Integer()
    letter_expired = fields.Boolean()

    # XXX: For maintaining UNIX TS for datetimes
    @pre_dump
    def eduid_datetime_encoder(self, in_data):
        dt = in_data.get('letter_expires')
        if dt:
            in_data['letter_expires'] = app.json_encoder().default(dt)
        return in_data


class VerifyCodeResponseSchema(BaseResponseSchema):

    success = fields.Boolean(required=True)
    data = fields.Nested(ProofingDataSchema, required=True)
# End output validation
