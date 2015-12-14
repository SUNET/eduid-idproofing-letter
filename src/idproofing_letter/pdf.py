from xhtml2pdf import pisa
from StringIO import StringIO
from idproofing_letter import app


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

    name = u'{GivenName} {SurName}'.format(**recipient.get('Name'))
    address = u'{}'.format(recipient.get('OfficialAddress').get('Address2'))
    postal_code = u'{PostalCode} {City}'.format(**recipient.get('OfficialAddress'))

    letter_template = render_template('letter.html',
                                      recipient_name=name,
                                      recipient_address=address,
                                      recipient_postal_code=postal_code,
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