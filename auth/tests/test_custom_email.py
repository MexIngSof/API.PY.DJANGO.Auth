from botocore.exceptions import ClientError
from django.test import SimpleTestCase

from auth.custom_email import classify_email_error


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
