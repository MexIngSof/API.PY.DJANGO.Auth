from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication

from access.models import Applications


class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request: Request):
        header = self.get_header(request)
        if header is not None:
            raw_token = self.get_raw_token(header)
        else:
            raw_token = request.COOKIES.get(settings.AUTH_COOKIE)

        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)

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
