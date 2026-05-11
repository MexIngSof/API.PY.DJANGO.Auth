from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

from access.models import PasswordHistory, RefreshTokens, UserDevices, UserSessions
from user.models import UserAccount


@receiver(pre_save, sender=UserAccount)
def revoke_access_on_password_change(sender, instance, **kwargs):
    if not instance.pk:
        return

    previous = sender.objects.filter(pk=instance.pk).only("password").first()
    if previous is None or previous.password == instance.password:
        return

    if not PasswordHistory.objects.filter(
        UserID=instance,
        PasswordHash=instance.password,
    ).exists():
        PasswordHistory.objects.create(
            UserID=instance,
            PasswordHash=instance.password,
        )
    now = timezone.now()

    UserSessions.objects.filter(UserID=instance, RevokedAt__isnull=True).update(
        RevokedAt=now,
        RevokedReason="PASSWORD_CHANGED",
        IsOnline=False,
    )
    RefreshTokens.objects.filter(UserID=instance, RevokedAt__isnull=True).update(
        RevokedAt=now,
        RevokedReason="PASSWORD_CHANGED",
    )
    UserDevices.objects.filter(UserID=instance, IsTrusted=True).update(
        IsTrusted=False,
        RevokedAt=now,
        RevokedReason="PASSWORD_CHANGED",
    )
