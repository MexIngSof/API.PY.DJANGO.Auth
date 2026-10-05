from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory

from user.application_scope import resolve_application_context


@override_settings(GATEWAY_INTERNAL_SHARED_SECRET="gateway-secret")
class TrustedApplicationContextTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def request(self, application_code="REFAPART", body=None, token="gateway-secret"):
        headers = {}
        if application_code is not None:
            headers["HTTP_X_APPLICATION_CODE"] = application_code
        if token is not None:
            headers["HTTP_X_GATEWAY_INTERNAL_TOKEN"] = token
        return self.factory.post("/api/auth/jwt/create/", body or {}, format="json", **headers)

    @patch("user.application_scope.Applications.objects.filter")
    def test_trusted_gateway_context_resolves_active_application(self, filter_mock):
        application = SimpleNamespace(ApplicationID=4, Code="REFAPART")
        filter_mock.return_value.only.return_value.first.return_value = application

        resolved = resolve_application_context(self.request())

        self.assertIs(resolved, application)
        filter_mock.assert_called_once_with(Code="REFAPART", IsActive=True)

    def test_missing_gateway_token_fails_closed(self):
        with self.assertRaises(AuthenticationFailed) as context:
            resolve_application_context(self.request(token=None))

        self.assertEqual(context.exception.get_codes(), "GATEWAY_CONTEXT_REQUIRED")

    def test_missing_application_header_fails_closed(self):
        with self.assertRaises(AuthenticationFailed) as context:
            resolve_application_context(self.request(application_code=None))

        self.assertEqual(context.exception.get_codes(), "APPLICATION_CODE_REQUIRED")

    @patch("user.application_scope.Applications.objects.filter")
    def test_unknown_application_fails_closed(self, filter_mock):
        filter_mock.return_value.only.return_value.first.return_value = None

        with self.assertRaises(AuthenticationFailed) as context:
            resolve_application_context(self.request("UNKNOWN"))

        self.assertEqual(context.exception.get_codes(), "APPLICATION_NOT_REGISTERED")

    @patch("user.application_scope.Applications.objects.filter")
    def test_conflicting_body_application_code_is_rejected(self, filter_mock):
        filter_mock.return_value.only.return_value.first.return_value = SimpleNamespace(
            ApplicationID=4,
            Code="REFAPART",
        )

        with self.assertRaises(AuthenticationFailed) as context:
            resolve_application_context(
                self.request(body={"ApplicationCode": "JOBCRON"})
            )

        self.assertEqual(context.exception.get_codes(), "APPLICATION_CONTEXT_MISMATCH")

    @patch("user.application_scope.Applications.objects.filter")
    def test_conflicting_body_application_id_is_rejected(self, filter_mock):
        filter_mock.return_value.only.return_value.first.return_value = SimpleNamespace(
            ApplicationID=4,
            Code="REFAPART",
        )

        with self.assertRaises(AuthenticationFailed) as context:
            resolve_application_context(self.request(body={"idApp": 9}))

        self.assertEqual(context.exception.get_codes(), "APPLICATION_CONTEXT_MISMATCH")
