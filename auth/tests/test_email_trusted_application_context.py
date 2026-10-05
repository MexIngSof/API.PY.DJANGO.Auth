from django.test import SimpleTestCase, override_settings
from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from unittest.mock import patch
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory

from auth.custom_email import get_application_code


@override_settings(GATEWAY_INTERNAL_SHARED_SECRET="test-gateway-secret")
class EmailTrustedApplicationContextTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    @patch("user.application_scope.Applications.objects.filter")
    def test_email_routing_uses_trusted_gateway_header_not_body(self, filter_mock):
        application = type("Application", (), {"ApplicationID": 1, "Code": "REFAPART"})()
        filter_mock.return_value.only.return_value.first.return_value = application
        request = Request(self.factory.post(
            "/api/auth/users/reset_password/",
            {"email": "user@example.com", "application_code": "JOBCRON"},
            format="json",
            HTTP_X_APPLICATION_CODE="REFAPART",
            HTTP_X_GATEWAY_INTERNAL_TOKEN="test-gateway-secret",
        ), parsers=[JSONParser()])

        with self.assertRaises(AuthenticationFailed) as context:
            get_application_code(request)

        self.assertEqual(context.exception.get_codes(), "APPLICATION_CONTEXT_MISMATCH")

    def test_email_routing_rejects_untrusted_gateway_context(self):
        request = Request(self.factory.post(
            "/api/auth/users/reset_password/",
            {"email": "user@example.com"},
            format="json",
            HTTP_X_APPLICATION_CODE="REFAPART",
        ), parsers=[JSONParser()])

        with self.assertRaises(AuthenticationFailed) as context:
            get_application_code(request)

        self.assertEqual(context.exception.get_codes(), "GATEWAY_CONTEXT_REQUIRED")
