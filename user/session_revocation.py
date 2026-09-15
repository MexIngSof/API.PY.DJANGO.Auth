import hashlib

from django.utils import timezone

from access.models import RefreshTokens


def token_hash(value):
    return hashlib.sha256((value or "").encode("utf-8")).hexdigest()


def tracked_refresh(value):
    if not value:
        return None
    return (
        RefreshTokens.objects.select_related("UserID", "SessionID", "SessionID__ApplicationID")
        .filter(TokenHash=token_hash(value))
        .order_by("-CreatedAt")
        .first()
    )


def tracked_refresh_is_revoked(record):
    return bool(
        record is not None
        and (
            record.RevokedAt is not None
            or (
                record.SessionID is not None
                and record.SessionID.RevokedAt is not None
            )
        )
    )


def revoke_tracked_refresh(value, *, reason="USER_LOGOUT"):
    record = tracked_refresh(value)
    if record is None:
        return None

    now_value = timezone.now()
    if record.RevokedAt is None:
        record.RevokedAt = now_value
        record.RevokedReason = reason
        record.save(update_fields=["RevokedAt", "RevokedReason"])

    session = record.SessionID
    if session is not None and session.RevokedAt is None:
        session.RevokedAt = now_value
        session.RevokedReason = reason
        session.IsOnline = False
        session.save(update_fields=["RevokedAt", "RevokedReason", "IsOnline"])

    return record
