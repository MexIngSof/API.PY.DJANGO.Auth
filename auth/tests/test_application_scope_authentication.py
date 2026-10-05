from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory

from user.authentication import CustomJWTAuthentication


@override_settings(GATEWAY_INTERNAL_SHARED_SECRET="test-context")
class ApplicationScopedAuthenticationTests(SimpleTestCase):
    def setUp(self):
        self.authentication = CustomJWTAuthentication()
        self.factory = APIRequestFactory()

    def request(self, application_code="REFAPART", gateway_context="test-context"):
        headers = {"HTTP_AUTHORIZATION": "Bearer test-token"}
        if application_code is not None:
            headers["HTTP_X_APPLICATION_CODE"] = application_code
        if gateway_context is not None:
            headers["HTTP_X_GATEWAY_INTERNAL_TOKEN"] = gateway_context
        return self.factory.get("/api/access/me/permissions/", **headers)

    def configure_token(self, user):
        self.authentication.get_validated_token = Mock(return_value={"token": True})
        self.authentication.get_user = Mock(return_value=user)

    @patch("user.application_scope.Applications.objects.filter")
    def test_matching_user_application_is_allowed(self, filter_mock):
        user = SimpleNamespace(id=17, idApp=4)
        self.configure_token(user)
        filter_mock.return_value.only.return_value.first.return_value = SimpleNamespace(
            ApplicationID=4,
            Code="REFAPART",
        )

        authenticated_user, _ = self.authentication.authenticate(self.request())

        self.assertIs(authenticated_user, user)
        filter_mock.assert_called_once_with(Code="REFAPART", IsActive=True)

    @patch("user.application_scope.Applications.objects.filter")
    def test_cross_application_request_fails_closed(self, filter_mock):
        user = SimpleNamespace(id=17, idApp=4)
        self.configure_token(user)
        filter_mock.return_value.only.return_value.first.return_value = SimpleNamespace(
            ApplicationID=9,
            Code="JOBCRON",
        )

        with self.assertRaises(AuthenticationFailed) as context:
            self.authentication.authenticate(self.request("JOBCRON"))

        self.assertEqual(context.exception.get_codes(), "APPLICATION_ACCESS_DENIED")

    @patch("user.application_scope.Applications.objects.filter")
    def test_unknown_or_inactive_application_fails_closed(self, filter_mock):
        user = SimpleNamespace(id=17, idApp=4)
        self.configure_token(user)
        filter_mock.return_value.only.return_value.first.return_value = None

        with self.assertRaises(AuthenticationFailed) as context:
            self.authentication.authenticate(self.request("UNKNOWN"))

        self.assertEqual(context.exception.get_codes(), "APPLICATION_NOT_REGISTERED")

    def test_request_without_application_header_fails_closed(self):
        user = SimpleNamespace(id=17, idApp=4)
        self.configure_token(user)

        with self.assertRaises(AuthenticationFailed) as context:
            self.authentication.authenticate(self.request(application_code=None))

        self.assertEqual(context.exception.get_codes(), "APPLICATION_CODE_REQUIRED")

    def test_request_without_trusted_gateway_context_fails_closed(self):
        user = SimpleNamespace(id=17, idApp=4)
        self.configure_token(user)

        with self.assertRaises(AuthenticationFailed) as context:
            self.authentication.authenticate(self.request(gateway_context=None))

        self.assertEqual(context.exception.get_codes(), "GATEWAY_CONTEXT_REQUIRED")
