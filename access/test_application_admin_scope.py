from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from access.application_admin_scope import resolve_admin_target_application
from access.models import Applications


@override_settings(GATEWAY_INTERNAL_SHARED_SECRET="admin-scope-test-secret")
class ApplicationAdminScopeTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.refapart, _ = Applications.objects.get_or_create(
            Code="REFAPART", defaults={"Name": "RefaPart", "IsActive": True}
        )
        self.jobcron, _ = Applications.objects.get_or_create(
            Code="JOBCRON", defaults={"Name": "JobCron", "IsActive": True}
        )
        User = get_user_model()
        self.delegated = User.objects.create_user(
            email="delegated@example.com",
            password="test-password",
            idApp=self.refapart.ApplicationID,
            is_staff=True,
        )
        self.global_admin = User.objects.create_superuser(
            email="global@example.com",
            password="test-password",
            idApp=self.refapart.ApplicationID,
        )

    def _request(self, user, target=None):
        query = {} if target is None else {"application_code": target}
        request = self.factory.get(
            "/api/access/identity/users/",
            data=query,
            HTTP_X_APPLICATION_CODE="REFAPART",
            HTTP_X_GATEWAY_INTERNAL_TOKEN="admin-scope-test-secret",
        )
        return self._as_request(request, user)

    @staticmethod
    def _as_request(request, user):
        drf_request = Request(request)
        drf_request.user = user
        return drf_request

    def test_delegated_admin_defaults_target_to_trusted_actor_application(self):
        target = resolve_admin_target_application(self._request(self.delegated))
        self.assertEqual(target.ApplicationID, self.refapart.ApplicationID)

    def test_delegated_admin_may_explicitly_target_same_application(self):
        target = resolve_admin_target_application(self._request(self.delegated, "REFAPART"))
        self.assertEqual(target.ApplicationID, self.refapart.ApplicationID)

    def test_delegated_admin_cannot_target_another_application(self):
        with self.assertRaisesMessage(PermissionDenied, "Delegated administrators"):
            resolve_admin_target_application(self._request(self.delegated, "JOBCRON"))

    def test_superadmin_may_target_another_registered_application(self):
        target = resolve_admin_target_application(self._request(self.global_admin, "JOBCRON"))
        self.assertEqual(target.ApplicationID, self.jobcron.ApplicationID)

    def test_superadmin_cannot_target_unknown_application(self):
        with self.assertRaisesMessage(NotFound, "not registered or active"):
            resolve_admin_target_application(self._request(self.global_admin, "UNKNOWN"))
