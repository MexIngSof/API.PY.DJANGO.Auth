from botocore.exceptions import ClientError
from django.test import SimpleTestCase

from auth.custom_email import classify_email_error, sanitize_email_error


class EmailErrorClassificationTests(SimpleTestCase):
    def test_ses_access_denied_is_classified_explicitly(self):
        error = ClientError(
            {
                "Error": {
                    "Code": "AccessDeniedException",
                    "Message": "User is not authorized to perform: ses:GetAccount",
                }
            },
            "GetAccount",
        )

        self.assertEqual(classify_email_error(error), "SES_ACCESS_DENIED")

    def test_ses_unverified_email_is_classified_before_region(self):
        error = Exception(
            "Email address is not verified. The following identities failed "
            "the check in region US-EAST-1: person@example.test"
        )

        self.assertEqual(classify_email_error(error), "SES_EMAIL_NOT_VERIFIED")

    def test_ses_error_sanitizes_email_addresses(self):
        message = sanitize_email_error(
            "The following identities failed the check: person@example.test",
            "person@example.test",
        )

        self.assertNotIn("person@example.test", message)
        self.assertIn("pe***n@example.test", message)
