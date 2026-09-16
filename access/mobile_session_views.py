import hashlib

from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response

from access.models import RefreshTokens, UserSessions
from access.views import OwnUserSessionViewSet, audit_session_event


def current_session_for_request(request):
    """Resolve the authenticated session for mobile bearer or Web cookie flows."""

    validated_token = getattr(request, "auth", None)
    token_jti = ""
    if validated_token is not None:
        try:
            token_jti = str(validated_token.get("jti") or "")
        except (AttributeError, TypeError):
            token_jti = ""

    if token_jti:
        session = (
            UserSessions.objects.filter(
                UserID=request.user,
                AccessTokenJti=token_jti,
                RevokedAt__isnull=True,
            )
            .order_by("-LastActivityAt")
            .first()
        )
        if session is not None:
            return session

    refresh_value = request.COOKIES.get("refresh")
    if not refresh_value:
        return None

    refresh_hash = hashlib.sha256(refresh_value.encode("utf-8")).hexdigest()
    return (
        UserSessions.objects.filter(
            UserID=request.user,
            RefreshTokenHash=refresh_hash,
            RevokedAt__isnull=True,
        )
        .order_by("-LastActivityAt")
        .first()
    )


class MobileOwnUserSessionViewSet(OwnUserSessionViewSet):
    """Own-session API with bearer-aware current-session semantics."""

    def get_serializer_context(self):
        context = super().get_serializer_context()
        current_session = current_session_for_request(self.request)
        context["current_session_id"] = (
            current_session.SessionID if current_session is not None else None
        )
        return context

    @action(detail=False, methods=["post"], url_path="revoke-all")
    def revoke_all(self, request):
        keep_current = bool(request.data.get("keep_current", False))
        current_session = current_session_for_request(request)
        queryset = self.get_queryset().filter(RevokedAt__isnull=True)
        if keep_current and current_session is not None:
            queryset = queryset.exclude(SessionID=current_session.SessionID)

        session_ids = list(queryset.values_list("SessionID", flat=True))
        now_value = timezone.now()
        updated = queryset.update(
            RevokedAt=now_value,
            RevokedReason="USER_REVOKED_ALL",
            IsOnline=False,
        )
        refresh_updated = RefreshTokens.objects.filter(
            UserID=request.user,
            SessionID_id__in=session_ids,
            RevokedAt__isnull=True,
        ).update(
            RevokedAt=now_value,
            RevokedReason="USER_REVOKED_ALL",
        )

        audit_session_event(
            request,
            "identity.sessions.revoked_all",
            session=current_session,
            metadata={
                "keep_current": keep_current,
                "revoked_sessions": updated,
                "revoked_refresh_tokens": refresh_updated,
            },
        )
        return Response(
            {
                "revoked_sessions": updated,
                "revoked_refresh_tokens": refresh_updated,
                "kept_current": keep_current and current_session is not None,
            }
        )
