import os
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, override_settings

from access.models import Applications
from roles.models import UserRoles
from user.models import UserAccount


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