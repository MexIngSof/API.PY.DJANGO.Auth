import hashlib

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.timezone import now
from djoser.compat import get_user_email
from djoser.conf import settings as djoser_settings
from djoser.views import UserViewSet
from djoser.social.views import ProviderAuthView
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from social_django.models import UserSocialAuth

from access.models import (
    AccessAuditEvents,
    Applications,
    LoginAttempts,
    PasswordHistory,
    RefreshTokens,
    SocialLoginAttempts,
    SocialProviders,
    UserSocialAccounts,
    UserDevices,
    UserSessions,
)
from user.application_scope import resolve_application_context


def get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def get_application_code(request):
    return resolve_application_context(request).Code


def sha256(value):
    return hashlib.sha256((value or "").encode("utf-8")).hexdigest()


def get_application(application_code):
    if not application_code:
        return None
    return Applications.objects.filter(Code=application_code, IsActive=True).first()


def get_social_provider(provider):
    backend_name = (provider or "").strip().lower()
    return SocialProviders.objects.filter(BackendName=backend_name, IsActive=True).first()


def record_access_event(request, event_type, user=None, application=None, metadata=None):
    AccessAuditEvents.objects.create(
        UserID=user,
        ApplicationID=application,
        EventType=event_type,
        IpAddress=get_client_ip(request),
        UserAgent=request.META.get("HTTP_USER_AGENT", ""),
        RequestId=request.headers.get("X-Request-ID", ""),
        CorrelationId=request.headers.get("X-Correlation-ID", ""),
        Metadata=metadata or {},
    )


def record_login_attempt(request, email, success, failure_reason="", user=None):
    LoginAttempts.objects.create(
        UserID=user,
        Email=email or "",
        ApplicationCode=get_application_code(request),
        IpAddress=get_client_ip(request),
        UserAgent=request.META.get("HTTP_USER_AGENT", ""),
        Success=success,
        FailureReason=failure_reason,
    )


def record_social_login_attempt(request, provider, email, success, failure_reason="", user=None):
    SocialLoginAttempts.objects.create(
        UserID=user,
        SocialProviderID=get_social_provider(provider),
        ApplicationCode=get_application_code(request),
        Email=email or "",
        IpAddress=get_client_ip(request),
        UserAgent=request.META.get("HTTP_USER_AGENT", ""),
        Success=success,
        FailureReason=failure_reason,
    )


def _extract_refresh_token(request, response):
    refresh_value = response.data.get("refresh") if hasattr(response, "data") else None
    if refresh_value:
        return refresh_value
    return request.COOKIES.get("refresh")


def _track_session(request, user, application, refresh_value):
    if not refresh_value or user is None or application is None:
        return None
    refresh = RefreshToken(refresh_value)
    session = UserSessions.objects.create(
        UserID=user,
        ApplicationID=application,
        IsOnline=True,
        IpAddress=get_client_ip(request),
        UserAgent=request.META.get("HTTP_USER_AGENT", ""),
    )
    RefreshTokens.objects.create(
        UserID=user,
        SessionID=session,
        JtiHash=sha256(str(refresh.get("jti", ""))),
        TokenHash=sha256(refresh_value),
        ExpiresAt=timezone.datetime.fromtimestamp(refresh["exp"], tz=timezone.utc),
    )
    return session


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request: Request, *args, **kwargs) -> Response:
        response = super().post(request, *args, **kwargs)
        email = (request.data.get("email") or "").strip().lower()
        user = get_user_model().objects.filter(email=email).first()
        if response.status_code == status.HTTP_200_OK:
            application = get_application(get_application_code(request))
            refresh_value = response.data.get("refresh")
            if user and application and user.idApp != application.ApplicationID:
                return Response(
                    {"code": "APPLICATION_ACCESS_DENIED", "detail": "Account does not belong to this application."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if refresh_value and application:
                refresh = RefreshToken(refresh_value)
                refresh["application_id"] = application.ApplicationID
                refresh["application_code"] = application.Code
                response.data["refresh"] = str(refresh)
                response.data["access"] = str(refresh.access_token)
                refresh_value = response.data["refresh"]
            session = _track_session(request, user, application, refresh_value)
            record_login_attempt(request, email, True, user=user)
            record_access_event(
                request,
                "identity.login.succeeded",
                user=user,
                application=application,
                metadata={"session_id": session.SessionID if session else None},
            )
            if user:
                response.data["user"] = {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "must_change_password": user.must_change_password,
                    "application": application.Code if application else "",
                }
        else:
            record_login_attempt(request, email, False, "invalid_credentials", user=user)
        return response


class RequiredPasswordChangeView(APIView):
    def post(self, request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return Response({"detail": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)

        application = resolve_application_context(request)
        if str(request.user.idApp) != str(application.ApplicationID):
            return Response(
                {"code": "APPLICATION_ACCESS_DENIED", "detail": "Account does not belong to this application."},
                status=status.HTTP_403_FORBIDDEN,
            )

        current_password = request.data.get("current_password") or request.data.get("currentPassword")
        new_password = request.data.get("new_password") or request.data.get("newPassword")
        re_new_password = request.data.get("re_new_password") or request.data.get("reNewPassword") or new_password
        if not current_password or not new_password:
            return Response({"detail": "current_password and new_password are required."}, status=status.HTTP_400_BAD_REQUEST)
        if new_password != re_new_password:
            return Response({"detail": "New password confirmation does not match."}, status=status.HTTP_400_BAD_REQUEST)
        if len(new_password) < 12:
            return Response({"detail": "New password must contain at least 12 characters."}, status=status.HTTP_400_BAD_REQUEST)
        if not request.user.check_password(current_password):
            return Response({"detail": "Current password is invalid."}, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(new_password)
        request.user.must_change_password = False
        request.user.save(update_fields=["password", "must_change_password"])
        PasswordHistory.objects.create(UserID=request.user, PasswordHash=request.user.password)
        record_access_event(request, "identity.password.changed", user=request.user, application=application, metadata={"required_change": True})
        return Response({"detail": "Password changed successfully."})


class CustomUserViewSet(UserViewSet):
    def reset_password(self, request, *args, **kwargs):
        email = (request.data.get("email") or "").strip().lower()
        application = get_application(get_application_code(request))
        User = get_user_model()
        user = User.objects.filter(email=email, is_active=True).first()
        setup_pending = bool(user and application and user.idApp == application.ApplicationID and user.must_change_password and not user.has_usable_password())
        if not setup_pending:
            return super().reset_password(request, *args, **kwargs)
        try:
            djoser_settings.EMAIL.password_reset(request, {"user": user}).send([user.email])
        except Exception:
            return Response({"code": "EMAIL_PROVIDER_UNAVAILABLE", "detail": "The access email could not be sent."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        record_access_event(request, "identity.password.setup.requested", user=user, application=application, metadata={"first_access": True})
        return Response(status=status.HTTP_204_NO_CONTENT)

    def reset_password_confirm(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        user.set_password(serializer.data["new_password"])
        user.must_change_password = False
        if hasattr(user, "last_login"):
            user.last_login = now()
        user.save()
        application = resolve_application_context(request)
        if str(user.idApp) != str(application.ApplicationID):
            return Response({"code": "APPLICATION_ACCESS_DENIED", "detail": "Account does not belong to this application."}, status=status.HTTP_403_FORBIDDEN)
        record_access_event(request, "identity.password.reset.confirmed", user=user, application=application, metadata={"must_change_password": False})
        if djoser_settings.PASSWORD_CHANGED_EMAIL_CONFIRMATION:
            context = {"user": user}
            to = [get_user_email(user)]
            djoser_settings.EMAIL.password_changed_confirmation(request, context).send(to)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request: Request, *args, **kwargs) -> Response:
        return super().post(request, *args, **kwargs)


class CustomTokenVerifyView(TokenVerifyView):
    pass


class CustomProviderAuthView(ProviderAuthView):
    def post(self, request, *args, **kwargs):
        provider = kwargs.get("provider")
        response = super().post(request, *args, **kwargs)
        email = (request.data.get("email") or "").strip().lower()
        success = response.status_code == status.HTTP_200_OK
        record_social_login_attempt(request, provider, email, success, "" if success else "provider_auth_failed")
        return response
