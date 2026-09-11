from django.test import TestCase

from access.models import ApplicationPermissions, RolePermissions
from roles.models import Roles


REQUIRED_PERMISSIONS = {
    "commercechannel.channels.read",
    "commercechannel.accounts.read",
    "commercechannel.accounts.manage",
    "commercechannel.accounts.validate",
    "commercechannel.accounts.credentials.rotate",
    "commercechannel.listings.read",
    "commercechannel.listings.create",
    "commercechannel.listings.update",
    "commercechannel.listings.publish",
    "commercechannel.listings.pause",
    "commercechannel.listings.sync",
    "commercechannel.mappings.read",
    "commercechannel.mappings.manage",
    "commercechannel.sync.read",
    "commercechannel.sync.run",
    "commercechannel.sync.retry",
    "commercechannel.webhooks.read",
    "commercechannel.webhooks.replay",
    "commercechannel.audit.read",
}


class CommerceChannelPermissionTests(TestCase):
    def test_channel_admin_has_complete_permission_catalog(self):
        role = Roles.objects.get(Name="CHANNEL_ADMIN")
        granted = set(
            RolePermissions.objects.filter(RoleID=role).values_list(
                "PermissionID__Code", flat=True
            )
        )
        self.assertEqual(granted, REQUIRED_PERMISSIONS)

    def test_viewer_is_default_read_only_subset(self):
        role = Roles.objects.get(Name="CHANNEL_VIEWER")
        granted = set(
            RolePermissions.objects.filter(RoleID=role).values_list(
                "PermissionID__Code", flat=True
            )
        )
        self.assertIn("commercechannel.channels.read", granted)
        self.assertIn("commercechannel.accounts.read", granted)
        self.assertNotIn("commercechannel.accounts.manage", granted)
        self.assertNotIn("commercechannel.accounts.credentials.rotate", granted)
        self.assertNotIn("commercechannel.webhooks.replay", granted)

    def test_registered_consumer_applications_expose_catalog(self):
        for code in ("JOBCRON", "REFAPART", "TECNOTELEC", "MEXINGSOF", "IMAGRAFITY"):
            granted = set(
                ApplicationPermissions.objects.filter(
                    ApplicationID__Code=code,
                    PermissionID__Code__in=REQUIRED_PERMISSIONS,
                ).values_list("PermissionID__Code", flat=True)
            )
            self.assertEqual(granted, REQUIRED_PERMISSIONS)
