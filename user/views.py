import hashlib

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
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


def get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def get_application_code(request):
    return (
        request.data.get("ApplicationCode")
        or request.data.get("application_code")
        or request.query_params.get("application_code")
        or request.headers.get("X-Application-Code")
        or ""
    ).strip().upper()


def sha256(value):
    return hashlib.sha256((value or "").encode("utf-8")).hexdigest()


def get_application(application_code):
    if not application_code:
        return None
    return Applications.objects.filter(Code=application_code, IsActive=True).first()


def get_social_provider(provider):
    backend_name = (provider or "").strip().lower()
    return SocialProviders.objects.filter(
        BackendName=backend_name,
        IsActive=True,
    ).first()


def get_token_claim(token, claim):
    if not token:
        return ""
    try:
        return str(token[claim])
    except Exception:
        return ""


def get_token_expiration(token):
    try:
        return timezone.datetime.fromtimestamp(
            token["exp"],
            tz=timezone.get_current_timezone(),
        )
    except Exception:
        return None


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


def record_social_login_attempt(
    request,
    provider,
    success,
    failure_reason="",
    user=None,
    email="",
):
    SocialLoginAttempts.objects.create(
        UserID=user,
        SocialProviderID=get_social_provider(provider),
        ApplicationCode=get_application_code(request),
        Email=email or getattr(user, "email", "") or "",
        IpAddress=get_client_ip(request),
        UserAgent=request.META.get("HTTP_USER_AGENT", ""),
        Success=success,
        FailureReason=failure_reason,
    )


def sync_social_account(provider, user):
    social_provider = get_social_provider(provider)
    if social_provider is None or user is None:
        return None

    social_auth = UserSocialAuth.objects.filter(
        user=user,
        provider=social_provider.BackendName,
    ).order_by("-id").first()

    if social_auth is None:
        return None

    extra_data = social_auth.extra_data or {}
    account, _ = UserSocialAccounts.objects.update_or_create(
        SocialProviderID=social_provider,
        ProviderUserId=str(social_auth.uid),
        defaults={
            "UserID": user,
            "Email": extra_data.get("email", getattr(user, "email", "")) or "",
            "DisplayName": (
                extra_data.get("name")
                or extra_data.get("full_name")
                or f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()
            ),
            "ProfileUrl": extra_data.get("profile") or extra_data.get("link") or "",
            "AvatarUrl": extra_data.get("picture") or extra_data.get("avatar_url") or "",
            "IsActive": True,
            "LastLoginAt": timezone.now(),
        },
    )
    return account


def record_access_event(request, event_type, user=None, application=None, metadata=None):
    AccessAuditEvents.objects.create(
        UserID=user,
        ApplicationID=application,
        EventType=event_type,
        IpAddress=get_client_ip(request),
        UserAgent=request.META.get("HTTP_USER_AGENT", ""),
        Metadata=metadata or {},
    )


def record_successful_session(request, user, access_token_value, refresh_token_value):
    application = get_application(get_application_code(request))
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    ip_address = get_client_ip(request)
    fingerprint_source = (
        request.headers.get("X-Device-Fingerprint")
        or f"{user.id}:{ip_address}:{user_agent}"
    )
    fingerprint_hash = sha256(fingerprint_source)

    device, _ = UserDevices.objects.update_or_create(
        UserID=user,
        FingerprintHash=fingerprint_hash,
        defaults={
            "DeviceName": request.headers.get("X-Device-Name", ""),
            "DeviceType": request.headers.get("X-Device-Type", ""),
            "OperatingSystem": request.headers.get("X-Device-OS", ""),
            "Browser": request.headers.get("X-Device-Browser", ""),
            "IpAddress": ip_address,
            "UserAgent": user_agent,
            "IsActive": True,
            "RevokedAt": None,
            "RevokedReason": "",
        },
    )

    access_token = AccessToken(access_token_value)
    refresh_token = RefreshToken(refresh_token_value)

    session = UserSessions.objects.create(
        UserID=user,
        DeviceID=device,
        ApplicationID=application,
        AccessTokenJti=get_token_claim(access_token, "jti"),
        RefreshTokenHash=sha256(refresh_token_value),
        ExpiresAt=get_token_expiration(refresh_token),
        IsOnline=True,
    )

    RefreshTokens.objects.create(
        UserID=user,
        SessionID=session,
        TokenHash=sha256(refresh_token_value),
        Jti=get_token_claim(refresh_token, "jti"),
        ExpiresAt=get_token_expiration(refresh_token),
    )

    record_access_event(
        request,
        "login.success",
        user=user,
        application=application,
        metadata={"session_id": session.SessionID},
    )


class CustomProviderAuthView(ProviderAuthView):
    def post(self, request, *args, **kwargs):
        provider = kwargs.get("provider", "")
        response = super().post(request, *args, **kwargs)

        if response.status_code == status.HTTP_201_CREATED:
            access_token = response.data.get("access")
            refresh_token = response.data.get("refresh")
            user = None

            if access_token:
                token = AccessToken(access_token)
                user_id = get_token_claim(token, "user_id")
                User = get_user_model()
                user = User.objects.filter(id=user_id).first()

            record_social_login_attempt(request, provider, True, user=user)
            sync_social_account(provider, user)

            if user and access_token and refresh_token:
                record_successful_session(request, user, access_token, refresh_token)

            response.set_cookie(
                "access",
                access_token,
                max_age=settings.AUTH_COOKIE_ACCESS_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE,
            )

            response.set_cookie(
                "refresh",
                refresh_token,
                max_age=settings.AUTH_COOKIE_REFRESH_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE,
            )
        else:
            record_social_login_attempt(
                request,
                provider,
                False,
                failure_reason="provider_auth_failed",
            )

        return response


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request: Request, *args, **kwargs) -> Response:
        email = (request.data.get("email") or "").strip().lower()
        response = super().post(request, *args, **kwargs)

        User = get_user_model()
        user = User.objects.filter(email=email).first()

        if response.status_code == status.HTTP_200_OK:
            access_token = response.data.get("access")
            refresh_token = response.data.get("refresh")

            record_login_attempt(request, email, True, user=user)
            if user and access_token and refresh_token:
                record_successful_session(request, user, access_token, refresh_token)

            response.set_cookie(
                "access",
                access_token,
                max_age=settings.AUTH_COOKIE_ACCESS_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE,
            )

            response.set_cookie(
                "refresh",
                refresh_token,
                max_age=settings.AUTH_COOKIE_REFRESH_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE,
            )
            if user:
                application = get_application(get_application_code(request))
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
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        current_password = request.data.get("current_password") or request.data.get("currentPassword")
        new_password = request.data.get("new_password") or request.data.get("newPassword")
        re_new_password = request.data.get("re_new_password") or request.data.get("reNewPassword") or new_password

        if not current_password or not new_password:
            return Response(
                {"detail": "current_password and new_password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if new_password != re_new_password:
            return Response(
                {"detail": "New password confirmation does not match."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(new_password) < 12:
            return Response(
                {"detail": "New password must contain at least 12 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not request.user.check_password(current_password):
            return Response(
                {"detail": "Current password is invalid."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(new_password)
        request.user.must_change_password = False
        request.user.save(update_fields=["password", "must_change_password"])
        PasswordHistory.objects.create(UserID=request.user, PasswordHash=request.user.password)
        record_access_event(
            request,
            "identity.password.changed",
            user=request.user,
            application=get_application(get_application_code(request)),
            metadata={"required_change": True},
        )
        return Response({"detail": "Password changed successfully."})


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request: Request, *args, **kwargs) -> Response:
        refresh_token = request.COOKIES.get("refresh")

        if refresh_token:
            request.data["refresh"] = refresh_token

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


class CustomTokenVerifyView(TokenVerifyView):
    def post(self, request: Request, *args, **kwargs) -> Response:
        access_token = request.COOKIES.get("access")

        if access_token:
            request.data["token"] = access_token

        return super().post(request, *args, **kwargs)


class LogoutView(APIView):
    def post(self, request, *args, **kwargs):
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie("access")
        response.delete_cookie("refresh")
        return response
