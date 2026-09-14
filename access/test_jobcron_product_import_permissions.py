from django.test import TestCase

from access.models import ApplicationPermissions, Applications, Permissions, RolePermissions
from roles.models import Roles


class JobCronProductImportPermissionContractTests(TestCase):
    permission_codes = {
        "jobcron.product_import.read",
        "jobcron.product_import.preview",
        "jobcron.product_import.validate",
        "jobcron.product_import.execute",
        "jobcron.product_import.retry",
        "jobcron.product_import.replay",
        "jobcron.product_import.cancel",
        "jobcron.product_import.admin",
    }

    def test_permissions_are_registered_for_jobcron(self):
        application = Applications.objects.get(Code="JOBCRON")
        registered = set(
            ApplicationPermissions.objects.filter(
                ApplicationID=application,
                PermissionID__Code__in=self.permission_codes,
            ).values_list("PermissionID__Code", flat=True)
        )

        self.assertEqual(registered, self.permission_codes)

    def test_super_admin_receives_all_product_import_permissions(self):
        role = Roles.objects.get(Name="JOBCRON_SUPER_ADMIN")
        granted = set(
            RolePermissions.objects.filter(
                RoleID=role,
                PermissionID__Code__in=self.permission_codes,
            ).values_list("PermissionID__Code", flat=True)
        )

        self.assertEqual(granted, self.permission_codes)

    def test_product_import_permissions_reuse_existing_action_taxonomy(self):
        actions = dict(
            Permissions.objects.filter(Code__in=self.permission_codes).values_list(
                "Code", "ActionID__Name"
            )
        )

        self.assertEqual(actions["jobcron.product_import.read"], "READ")
        self.assertEqual(actions["jobcron.product_import.preview"], "READ")
        for code in {
            "jobcron.product_import.validate",
            "jobcron.product_import.execute",
            "jobcron.product_import.retry",
            "jobcron.product_import.replay",
            "jobcron.product_import.cancel",
        }:
            self.assertEqual(actions[code], "EXECUTE")
        self.assertEqual(actions["jobcron.product_import.admin"], "MANAGE")
