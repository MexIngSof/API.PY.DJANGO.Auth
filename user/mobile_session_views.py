from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .application_scope import resolve_application_context
from .session_revocation import (
    revoke_tracked_refresh,
    tracked_refresh,
    tracked_refresh_is_revoked,
)
from .views import record_access_event


def _tracked_application(tracked):
    session = getattr(tracked, "SessionID", None)
    return getattr(session, "ApplicationID", None) if session is not None else None


def _application_matches(application, candidate):
    return candidate is not None and str(candidate.ApplicationID) == str(application.ApplicationID)


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        application = resolve_application_context(request)
        refresh_value = request.COOKIES.get("refresh") or request.data.get("refresh")
        if not refresh_value:
            return Response(
                {"code": "REFRESH_TOKEN_REQUIRED", "detail": "Refresh token is required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            refresh_token = RefreshToken(refresh_value)
        except TokenError:
            return Response(
                {"code": "INVALID_REFRESH_TOKEN", "detail": "Refresh token is invalid."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token_application_id = refresh_token.get("application_id")
        token_application_code = str(refresh_token.get("application_code") or "").strip().upper()
        if token_application_id is None or not token_application_code:
            return Response(
                {"code": "TOKEN_APPLICATION_REQUIRED", "detail": "Refresh token is not bound to an application."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if (
            str(token_application_id) != str(application.ApplicationID)
            or token_application_code != application.Code.upper()
        ):
            return Response(
                {"code": "APPLICATION_ACCESS_DENIED", "detail": "Refresh token belongs to a different application."},
                status=status.HTTP_403_FORBIDDEN,
            )

        tracked = tracked_refresh(refresh_value)
        if tracked_refresh_is_revoked(tracked):
            return Response(
                {"code": "REFRESH_REVOKED", "detail": "The refresh token or its session has been revoked."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if tracked is not None and not _application_matches(application, _tracked_application(tracked)):
            return Response(
                {"code": "APPLICATION_ACCESS_DENIED", "detail": "Tracked refresh token belongs to a different application."},
                status=status.HTTP_403_FORBIDDEN,
            )

        request.data["refresh"] = refresh_value
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            access_token = response.data.get("access")
            if access_token:
                response.set_cookie(
                    "access",
                    access_token,
                    max_age=settings.AUTH_COOKIE_ACCESS_MAX_AGE,
                    path=settings.AUTH_COOKIE_PATH,
                    secure=settings.AUTH_COOKIE_SECURE,
                    httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                    samesite=settings.AUTH_COOKIE_SAMESITE,
                )
        return response


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        application = resolve_application_context(request)
        refresh_value = request.COOKIES.get("refresh") or request.data.get("refresh")
        tracked = tracked_refresh(refresh_value) if refresh_value else None
        if tracked is not None and not _application_matches(application, _tracked_application(tracked)):
            return Response(
                {"code": "APPLICATION_ACCESS_DENIED", "detail": "Refresh token belongs to a different application."},
                status=status.HTTP_403_FORBIDDEN,
            )

        tracked = revoke_tracked_refresh(refresh_value)
        if tracked is not None:
            session = tracked.SessionID
            record_access_event(
                request,
                "identity.session.logout",
                user=tracked.UserID,
                application=application,
                metadata={
                    "session_id": session.SessionID if session is not None else None,
                    "refresh_token_id": tracked.RefreshTokenID,
                },
            )

        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie("access")
        response.delete_cookie("refresh")
        return response
