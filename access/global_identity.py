"""Application-account correlation without SSO semantics."""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from access.models import GlobalIdentities, GlobalIdentityAccounts


@transaction.atomic
def link_account(*, global_identity, user, application):
    """Create an unverified, inactive correlation for an application account."""
    if user.idApp != application.ApplicationID:
        raise ValidationError("APPLICATION_ACCOUNT_MISMATCH")
    link, created = GlobalIdentityAccounts.objects.get_or_create(
        UserID=user,
        defaults={
            "GlobalIdentityID": global_identity,
            "ApplicationID": application,
            "IsVerified": False,
            "IsActive": False,
        },
    )
    if not created and link.GlobalIdentityID_id != global_identity.GlobalIdentityID:
        raise ValidationError("GLOBAL_IDENTITY_ACCOUNT_ALREADY_LINKED")
    return link


@transaction.atomic
def verify_link(*, global_identity, user, application):
    link = GlobalIdentityAccounts.objects.select_for_update().get(
        GlobalIdentityID=global_identity,
        UserID=user,
        ApplicationID=application,
        UnlinkedAt__isnull=True,
    )
    link.IsVerified = True
    link.IsActive = True
    link.VerifiedAt = timezone.now()
    link.save(update_fields=("IsVerified", "IsActive", "VerifiedAt", "UpdatedAt"))
    return link


@transaction.atomic
def unlink_account(*, global_identity, user, application):
    link = GlobalIdentityAccounts.objects.select_for_update().get(
        GlobalIdentityID=global_identity,
        UserID=user,
        ApplicationID=application,
        UnlinkedAt__isnull=True,
    )
    link.IsActive = False
    link.UnlinkedAt = timezone.now()
    link.save(update_fields=("IsActive", "UnlinkedAt", "UpdatedAt"))
    return link
