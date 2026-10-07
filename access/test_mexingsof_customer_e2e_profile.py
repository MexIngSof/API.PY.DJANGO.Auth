import os
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from access.models import ApplicationRolePermissions, Applications
from access.scoped_rbac_views import ApplicationScopedMePermissionsViewSet
from roles.models import UserRoles
from user.models import UserAccount


@override_settings(GATEWAY_INTERNAL_SHARED_SECRET="rbac-test-secret")
class MexIngSofCustomerE2EProfileTests(TestCase):
    @override_settings(DEVELOPMENT_MODE=True)
    def test_seeder_creates_separate_scoped_setup_and_limited_identities(self):
        env = {
            "AUTH_E2E_MEXINGSOF_ADMIN_USER": "auth-e2e-mexingsof-admin@example.local",
            "AUTH_E2E_MEXINGSOF_ADMIN_PASSWORD": "synthetic-admin-password",
            "AUTH_E2E_MEXINGSOF_LIMITED_USER": "auth-e2e-mexingsof-limited@example.local",
            "AUTH_E2E_MEXINGSOF_LIMITED_PASSWORD": "synthetic-limited-password",
            "AUTH_E2E_MEXINGSOF_USER": "auth-e2e-mexingsof-limited@example.local",
            "AUTH_E2E_MEXINGSOF_PASSWORD": "synthetic-limited-password",
        }
        output = StringIO()
        with patch.dict(os.environ, env, clear=False):
            call_command("seed_auth_e2e_users", applications="MEXINGSOF", stdout=output)
            call_command("seed_auth_e2e_users", applications="MEXINGSOF", stdout=output)

        application = Applications.objects.get(Code="MEXINGSOF")
        setup_admin = UserAccount.objects.get(email=env["AUTH_E2E_MEXINGSOF_ADMIN_USER"])
        limited = UserAccount.objects.get(email=env["AUTH_E2E_MEXINGSOF_LIMITED_USER"])
        self.assertEqual(setup_admin.idApp, application.ApplicationID)
        self.assertTrue(setup_admin.is_staff)
        self.assertFalse(setup_admin.is_superuser)
        self.assertEqual(limited.idApp, application.ApplicationID)
        self.assertFalse(limited.is_staff)
        self.assertFalse(limited.is_superuser)
        self.assertEqual(
            set(UserRoles.objects.filter(UserID=setup_admin).values_list("RoleID__Name", flat=True)),
            {"MEXINGSOF_SETUP_ADMIN"},
        )
        self.assertEqual(
            set(UserRoles.objects.filter(UserID=limited).values_list("RoleID__Name", flat=True)),
            {"CUSTOMER"},
        )
        self.assertEqual(
            set(
                ApplicationRolePermissions.objects.filter(
                    ApplicationID=application,
                    RoleID__Name="CUSTOMER",
                ).values_list("PermissionID__Code", flat=True)
            ),
            {"customer.read", "customer.write"},
        )
        self.assertNotIn(env["AUTH_E2E_MEXINGSOF_ADMIN_PASSWORD"], output.getvalue())
        self.assertNotIn(env["AUTH_E2E_MEXINGSOF_LIMITED_PASSWORD"], output.getvalue())
        self.assertNotIn("token=", output.getvalue().lower())

        request = APIRequestFactory().get(
            "/api/access/me/permissions/",
            HTTP_X_APPLICATION_CODE="MEXINGSOF",
            HTTP_X_GATEWAY_INTERNAL_TOKEN="rbac-test-secret",
        )
        force_authenticate(request, user=limited)
        response = ApplicationScopedMePermissionsViewSet.as_view(
            {"get": "list_permissions"}
        )(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["permissions"],
            [
                {"code": "customer.read", "allow": True},
                {"code": "customer.write", "allow": True},
            ],
        )

    @override_settings(DEVELOPMENT_MODE=False)
    def test_e2e_seeder_is_blocked_outside_local_development(self):
        output = StringIO()
        with patch.dict(os.environ, {"AUTH_E2E_ALLOW_NON_LOCAL": ""}, clear=False):
            with self.assertRaisesMessage(CommandError, "blocked outside local/DEV"):
                call_command("seed_auth_e2e_users", applications="MEXINGSOF", stdout=output)
