from xhtml2pdf import pisa
from StringIO import StringIO
from datetime import timedelta
from eduid_common.api.exceptions import ApiException
from idproofing_letter import app


def format_address(recipient):
    """
    :param recipient: official address
    :type recipient: OrderedDict
    :return: name, address, postal code
    :rtype: tuple
    """
    try:
        # TODO: Take GivenNameMarking in to account
        given_name = recipient.get('Name')['GivenName']               # Mandatory
        middle_name = recipient.get('Name').get('MiddleName', '')     # Optional
        surname = recipient.get('Name')['Surname']                    # Mandatory
        name = u'{!s} {!s} {!s}'.format(given_name, middle_name, surname)
        # TODO: Take eventual CareOf and Address1(?) in to account
        address = recipient.get('OfficialAddress')['Address2']        # Mandatory
        postal_code = recipient.get('OfficialAddress')['PostalCode']  # Mandatory
        city = recipient.get('OfficialAddress')['City']               # Mandatory
        return name, address, postal_code, city
    except (KeyError, TypeError, AttributeError) as e:
        app.logger.error('Postal address formatting failed: {!r}'.format(e))
        raise ApiException(payload={'errors': 'Postal address formatting failed: {!r}'.format(e)}, status_code=500)


def create_pdf(recipient, verification_code, created_timestamp):
    """
    Create a letter in the form of a PDF-document,
    containing a verification code to be sent to a user.

    :param recipient: Official address the letter should be sent to
    :param verification_code: Verification code to include in the letter
    :param created_timestamp: Timestamp for when the proofing was initiated
    """
    # Imported here to avoid exposing
    # render_template to the calling function.
    from flask import render_template

    pisa.showLogging()

    name, address, postal_code, city = format_address(recipient)

    # Calculate the validity period of the verification
    # code that is to be shown in the letter.
    max_wait = timedelta(hours=app.config['LETTER_WAIT_TIME_HOURS'])
    validity_period = (created_timestamp + max_wait).strftime('%Y-%m-%d')

    letter_template = render_template('letter.html',
                                      recipient_name=name,
                                      recipient_address=address,
                                      recipient_postal_code=postal_code,
                                      recipient_city=city,
                                      recipient_verification_code=verification_code,
                                      recipient_validity_period=validity_period)

    if app.config.get("EKOPOST_DEBUG_PDF", None):
        pdf_document = open(app.config.get("EKOPOST_DEBUG_PDF"), "w")
        pisa.CreatePDF(StringIO(letter_template), pdf_document)
    else:
        pdf_document = StringIO()
        pisa.CreatePDF(StringIO(letter_template), pdf_document)

        # Only return the document if it should be sent to Ekopost,
        # since in debug mode we only want to have it printed locally.
        return pdf_document