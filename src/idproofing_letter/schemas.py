# -*- coding: utf-8 -*-

from marshmallow import Schema, fields
from eduid_common.api.schemas.proofing_data import LetterProofingDataSchema
from eduid_common.api.schemas.validators import validate_nin

__author__ = 'lundberg'


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
    letter_expires = fields.DateTime(format='%s')
    letter_expired = fields.Boolean()


class VerifyCodeResponseSchema(BaseResponseSchema):

    success = fields.Boolean(required=True)
    data = fields.Nested(LetterProofingDataSchema, required=True)
# End output validation
