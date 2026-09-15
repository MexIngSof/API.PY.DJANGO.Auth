from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication

from access.models import Applications, UserSessions


class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request: Request):
        header = self.get_header(request)
        if header is not None:
            raw_token = self.get_raw_token(header)
        else:
            raw_token = request.COOKIES.get(settings.AUTH_COOKIE)

        # Django delete_cookie() leaves an empty cookie value in some clients.
        # Empty credentials mean unauthenticated, not an invalid JWT.
        if not raw_token:
            return None

        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)

        token_jti = str(validated_token.get("jti") or "")
        if token_jti:
            tracked_session = (
                UserSessions.objects.filter(
                    UserID=user,
                    AccessTokenJti=token_jti,
                )
                .only("SessionID", "RevokedAt", "IsOnline")
                .order_by("-StartedAt")
                .first()
            )
            if tracked_session is not None and tracked_session.RevokedAt is not None:
                raise AuthenticationFailed(
                    "The authenticated session has been revoked.",
                    code="SESSION_REVOKED",
                )

        application_code = str(
            request.headers.get("X-Application-Code") or ""
        ).strip().upper()
        if application_code:
            application = Applications.objects.filter(
                Code=application_code,
                IsActive=True,
            ).only("ApplicationID").first()
            if application is None:
                raise AuthenticationFailed(
                    "Requested application is not registered or active.",
                    code="APPLICATION_NOT_REGISTERED",
                )
            if int(user.idApp) != int(application.ApplicationID):
                raise AuthenticationFailed(
                    "Authenticated user does not belong to the requested application.",
                    code="APPLICATION_ACCESS_DENIED",
                )

        return user, validated_token
