from importlib import import_module

from django.apps import apps
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from access.models import (
    ApplicationPermissions,
    ApplicationRolePermissions,
    ApplicationRoles,
    Applications,
    Permissions,
    RolePermissions,
)
from access.scoped_rbac_views import ApplicationScopedMePermissionsViewSet
from roles.models import Roles
from roles.models import UserRoles


EXPECTED_PERMISSIONS = {
    "customer.read",
    "customer.view",
    "customer.create",
    "customer.write",
    "customer.admin",
}


@override_settings(GATEWAY_INTERNAL_SHARED_SECRET="rbac-test-secret")
class CustomerEnterprisePermissionSeedTests(TestCase):
    def test_jobcron_exposes_customer_enterprise_permissions(self):
        application = Applications.objects.get(Code="JOBCRON")
        assigned = set(
            ApplicationPermissions.objects.filter(ApplicationID=application).values_list(
                "PermissionID__Code", flat=True
            )
        )
        self.assertTrue(EXPECTED_PERMISSIONS.issubset(assigned))

    def test_mexingsof_exposes_only_capture_read_and_write_permissions(self):
        application = Applications.objects.get(Code="MEXINGSOF")
        assigned = set(
            ApplicationPermissions.objects.filter(ApplicationID=application).values_list(
                "PermissionID__Code", flat=True
            )
        )
        self.assertEqual(assigned.intersection(EXPECTED_PERMISSIONS), {"customer.read", "customer.write"})

        application_role_ids = ApplicationRoles.objects.filter(
            ApplicationID=application
        ).values_list("RoleID", flat=True)
        self.assertFalse(
            RolePermissions.objects.filter(
                RoleID__in=application_role_ids,
                PermissionID__Code__in={"customer.read", "customer.write"},
            ).exists()
        )

    def test_mexingsof_customer_role_receives_exactly_capture_read_and_write(self):
        application = Applications.objects.get(Code="MEXINGSOF")
        customer = Roles.objects.get(Name="CUSTOMER")
        assigned = set(
            ApplicationRolePermissions.objects.filter(
                ApplicationID=application,
                RoleID=customer,
            ).values_list("PermissionID__Code", flat=True)
        )
        self.assertEqual(assigned, {"customer.read", "customer.write"})

    def test_mexingsof_customer_role_permission_seed_is_idempotent(self):
        seed = import_module(
            "access.migrations.0043_seed_mexingsof_customer_role_permissions"
        ).seed_mexingsof_customer_role_permissions
        application = Applications.objects.get(Code="MEXINGSOF")
        customer = Roles.objects.get(Name="CUSTOMER")

        seed(apps, None)
        seed(apps, None)

        assigned = set(
            ApplicationRolePermissions.objects.filter(
                ApplicationID=application,
                RoleID=customer,
            ).values_list("PermissionID__Code", flat=True)
        )
        self.assertEqual(assigned, {"customer.read", "customer.write"})

    def test_other_application_customer_does_not_inherit_mexingsof_grants(self):
        application = Applications.objects.get(Code="TECNOTELEC")
        customer = Roles.objects.get(Name="CUSTOMER")
        user = get_user_model().objects.create_user(
            email="tecnotelec-customer-rbac@example.local",
            password="test-password",
            idApp=application.ApplicationID,
        )
        UserRoles.objects.get_or_create(UserID=user, RoleID=customer)
        permissions = list(Permissions.objects.filter(Code__in={"customer.read", "customer.write"}))
        for permission in permissions:
            ApplicationPermissions.objects.get_or_create(
                ApplicationID=application,
                PermissionID=permission,
            )

        request = APIRequestFactory().get(
            "/api/access/me/permissions/",
            HTTP_X_APPLICATION_CODE="TECNOTELEC",
            HTTP_X_GATEWAY_INTERNAL_TOKEN="rbac-test-secret",
        )
        force_authenticate(request, user=user)
        response = ApplicationScopedMePermissionsViewSet.as_view(
            {"get": "list_permissions"}
        )(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["permissions"], [])

    def test_only_jobcron_super_admin_receives_default_customer_enterprise_grant(self):
        super_admin = Roles.objects.get(Name="JOBCRON_SUPER_ADMIN")
        assigned = set(
            RolePermissions.objects.filter(RoleID=super_admin).values_list(
                "PermissionID__Code", flat=True
            )
        )
        self.assertTrue(EXPECTED_PERMISSIONS.issubset(assigned))


        other_roles = set(
            RolePermissions.objects.filter(PermissionID__Code__in=EXPECTED_PERMISSIONS)
            .exclude(RoleID=super_admin)
            .values_list("RoleID__Name", flat=True)
        )
        self.assertEqual(other_roles, set())

    def test_permissions_are_owned_by_customer_enterprise_identity_module(self):
        rows = Permissions.objects.filter(Code__in=EXPECTED_PERMISSIONS)
        self.assertEqual(rows.count(), len(EXPECTED_PERMISSIONS))
        self.assertEqual(
            set(rows.values_list("ModuleID__Code", flat=True)),
            {"CUSTOMER_ENTERPRISE_IDENTITY"},
        )
        self.assertEqual(
            set(rows.values_list("ModuleID__Path", flat=True)),
            {"/api/v1/core/customer/v2"},
        )

    def test_customer_facing_application_roles_do_not_gain_enterprise_admin_by_default(self):
        protected_roles = {
            "REFAPART_ADMIN",
            "REFAPART_CUSTOMER",
            "CUSTOMER",
            "JOBCRON_SUPPORT_ADMIN",
            "JOBCRON_PLATFORM_ADMIN",
        }
        granted = set(
            RolePermissions.objects.filter(
                PermissionID__Code__in=EXPECTED_PERMISSIONS,
                RoleID__Name__in=protected_roles,
            ).values_list("RoleID__Name", flat=True)
        )
        self.assertEqual(granted, set())
