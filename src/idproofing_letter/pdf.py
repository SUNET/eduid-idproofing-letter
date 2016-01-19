from xhtml2pdf import pisa
from StringIO import StringIO
from idproofing_letter.exceptions import ApiException
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
        address = recipient.get('OfficialAddress').get('Address2')
        postal_code = recipient.get('OfficialAddress').get('PostalCode')
        city = recipient.get('OfficialAddress').get('City')
        return name, address, postal_code, city
    except (KeyError, TypeError, AttributeError) as e:
        app.logger.error('Postal address formatting failed: {!r}'.format(e))
        raise ApiException({'errors': 'Postal address formatting failed: {!r}'.format(e)}, status_code=500)


def create_pdf(recipient, verification_code):
    """
    Create a letter in the form of a PDF-document,
    containing a verification code to be sent to a user.

    :param recipient: Official address the letter should be sent to
    :param verification_code: Verification code to include in the letter
    """
    # imported here to avoid exposing
    # render_template to the calling function.
    from flask import render_template

    pisa.showLogging()

    name, address, postal_code, city = format_address(recipient)

    letter_template = render_template('letter.html',
                                      recipient_name=name,
                                      recipient_address=address,
                                      recipient_postal_code=postal_code,
                                      recipient_city=city,
                                      code=verification_code)

    if app.config.get("EKOPOST_DEBUG_PDF", None):
        pdf_document = open(app.config.get("EKOPOST_DEBUG_PDF"), "w")
        pisa.CreatePDF(StringIO(letter_template), pdf_document)
    else:
        pdf_document = StringIO()
        pisa.CreatePDF(StringIO(letter_template), pdf_document)

        # Only return the document if it should be sent to Ekopost,
        # since in debug mode we only want to have it printed locally.
        return pdf_document