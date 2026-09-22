from django.test import TestCase

from roles.models import Roles

from .models import (
    ApplicationPermissions,
    Applications,
    Permissions,
    RolePermissions,
)


class TecnoTelecEconomicPermissionsTests(TestCase):
    def test_economic_permissions_are_registered_for_tecnotelec(self):
        application = Applications.objects.get(Code="TECNOTELEC")
        expected = {
            "tecnotelec.economics.read",
            "tecnotelec.economics.cost.read",
            "tecnotelec.economics.returns.read",
            "tecnotelec.economics.allocations.read",
            "tecnotelec.economics.scenarios.read",
            "tecnotelec.economics.admin",
        }

        registered = set(
            ApplicationPermissions.objects.filter(
                ApplicationID=application,
                PermissionID__Code__in=expected,
            ).values_list("PermissionID__Code", flat=True)
        )

        self.assertEqual(registered, expected)
        self.assertEqual(
            Permissions.objects.filter(Code__in=expected).count(),
            len(expected),
        )

    def test_customer_role_receives_no_economic_permissions_by_default(self):
        customer = Roles.objects.get(Name="CUSTOMER")
        expected = {
            "tecnotelec.economics.read",
            "tecnotelec.economics.cost.read",
            "tecnotelec.economics.returns.read",
            "tecnotelec.economics.allocations.read",
            "tecnotelec.economics.scenarios.read",
            "tecnotelec.economics.admin",
        }

        self.assertFalse(
            RolePermissions.objects.filter(
                RoleID=customer,
                PermissionID__Code__in=expected,
            ).exists()
        )
