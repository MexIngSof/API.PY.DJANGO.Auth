from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView

from .session_revocation import (
    revoke_tracked_refresh,
    tracked_refresh,
    tracked_refresh_is_revoked,
)
from .views import record_access_event


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_value = request.COOKIES.get("refresh") or request.data.get("refresh")
        tracked = tracked_refresh(refresh_value)

        if tracked_refresh_is_revoked(tracked):
            return Response(
                {
                    "code": "REFRESH_REVOKED",
                    "detail": "The refresh token or its session has been revoked.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if refresh_value:
            request.data["refresh"] = refresh_value

        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            access_token = response.data.get("access")
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
        refresh_value = request.COOKIES.get("refresh") or request.data.get("refresh")
        tracked = revoke_tracked_refresh(refresh_value)

        if tracked is not None:
            session = tracked.SessionID
            record_access_event(
                request,
                "identity.session.logout",
                user=tracked.UserID,
                application=(session.ApplicationID if session is not None else None),
                metadata={
                    "session_id": session.SessionID if session is not None else None,
                    "refresh_token_id": tracked.RefreshTokenID,
                },
            )

        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie("access")
        response.delete_cookie("refresh")
        return response
