"""Explicit application-account correlation without SSO semantics."""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from access.global_identity_models import GlobalIdentityAccounts
from access.models import AccessAuditEvents


def _assert_account_application(*, user, application):
    if user.idApp != application.ApplicationID:
        raise ValidationError("APPLICATION_ACCOUNT_MISMATCH")


def _audit(*, event_type, user, application, global_identity, link):
    AccessAuditEvents.objects.create(
        UserID=user,
        ApplicationID=application,
        EventType=event_type,
        Metadata={
            "global_identity_id": global_identity.GlobalIdentityID,
            "global_identity_account_id": link.GlobalIdentityAccountID,
        },
    )


@transaction.atomic
def link_account(*, global_identity, user, application):
    """Create an explicit unverified correlation for exactly one application account."""
    _assert_account_application(user=user, application=application)
    if not global_identity.IsActive:
        raise ValidationError("GLOBAL_IDENTITY_INACTIVE")

    existing = (
        GlobalIdentityAccounts.objects.select_for_update()
        .filter(UserID=user, UnlinkedAt__isnull=True)
        .first()
    )
    if existing is not None:
        if existing.GlobalIdentityID_id != global_identity.GlobalIdentityID:
            raise ValidationError("GLOBAL_IDENTITY_ACCOUNT_ALREADY_LINKED")
        if existing.ApplicationID_id != application.ApplicationID:
            raise ValidationError("APPLICATION_ACCOUNT_MISMATCH")
        return existing

    if GlobalIdentityAccounts.objects.select_for_update().filter(
        GlobalIdentityID=global_identity,
        ApplicationID=application,
        UnlinkedAt__isnull=True,
    ).exists():
        raise ValidationError("GLOBAL_IDENTITY_APPLICATION_ALREADY_LINKED")

    link = GlobalIdentityAccounts.objects.create(
        GlobalIdentityID=global_identity,
        UserID=user,
        ApplicationID=application,
        IsVerified=False,
        IsActive=False,
    )
    _audit(
        event_type="global_identity.link.requested",
        user=user,
        application=application,
        global_identity=global_identity,
        link=link,
    )
    return link


@transaction.atomic
def verify_link(*, global_identity, user, application):
    _assert_account_application(user=user, application=application)
    link = GlobalIdentityAccounts.objects.select_for_update().get(
        GlobalIdentityID=global_identity,
        UserID=user,
        ApplicationID=application,
        UnlinkedAt__isnull=True,
    )
    if link.IsActive and link.IsVerified:
        return link
    if GlobalIdentityAccounts.objects.select_for_update().filter(
        UserID=user,
        IsActive=True,
    ).exclude(pk=link.pk).exists():
        raise ValidationError("GLOBAL_IDENTITY_ACCOUNT_ALREADY_LINKED")
    if GlobalIdentityAccounts.objects.select_for_update().filter(
        GlobalIdentityID=global_identity,
        ApplicationID=application,
        IsActive=True,
    ).exclude(pk=link.pk).exists():
        raise ValidationError("GLOBAL_IDENTITY_APPLICATION_ALREADY_LINKED")

    link.IsVerified = True
    link.IsActive = True
    link.VerifiedAt = timezone.now()
    link.save(update_fields=("IsVerified", "IsActive", "VerifiedAt", "UpdatedAt"))
    _audit(
        event_type="global_identity.link.verified",
        user=user,
        application=application,
        global_identity=global_identity,
        link=link,
    )
    return link


@transaction.atomic
def unlink_account(*, global_identity, user, application):
    _assert_account_application(user=user, application=application)
    link = GlobalIdentityAccounts.objects.select_for_update().get(
        GlobalIdentityID=global_identity,
        UserID=user,
        ApplicationID=application,
        UnlinkedAt__isnull=True,
    )
    link.IsActive = False
    link.UnlinkedAt = timezone.now()
    link.save(update_fields=("IsActive", "UnlinkedAt", "UpdatedAt"))
    _audit(
        event_type="global_identity.unlinked",
        user=user,
        application=application,
        global_identity=global_identity,
        link=link,
    )
    return link
