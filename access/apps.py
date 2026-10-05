from django.apps import AppConfig


class AccessConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "access"

    def ready(self):
        # Global identity is intentionally isolated from the legacy access model
        # module while the multi-application identity schema is stabilized. The
        # classes still belong to the access app and are exported on
        # access.models for compatibility with existing owner contracts.
        from access import models as access_models
        from access.global_identity_models import GlobalIdentities, GlobalIdentityAccounts

        access_models.GlobalIdentities = GlobalIdentities
        access_models.GlobalIdentityAccounts = GlobalIdentityAccounts
