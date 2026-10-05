from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from djoser.compat import get_user_email
from djoser.conf import settings as djoser_settings
from djoser.utils import decode_uid
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from user.account_scope import (
    account_belongs_to_application,
    find_local_account,
    normalize_email,
)
from user.application_scope import resolve_application_context
from user.serializers import ApplicationScopedTokenObtainPairSerializer
from user.views import (
    CustomUserViewSet,
    record_access_event,
    record_login_attempt,
    record_successful_session,
)


class ApplicationScopedTokenObtainPairView(TokenObtainPairView):
    serializer_class = ApplicationScopedTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        application = resolve_application_context(request)
        email = normalize_email(request.data.get("email"))
        user = find_local_account(application, email)

        if (
            user
            and user.is_active
            and user.must_change_password
            and not user.has_usable_password()
        ):
            record_login_attempt(
                request,
                email,
                False,
                "password_setup_required",
                user=user,
            )
            return Response(
                {
                    "code": "PASSWORD_SETUP_REQUIRED",
                    "detail": "Password setup is required before login.",
                },
                status=status.HTTP_409_CONFLICT,
            )

        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            access_token = response.data.get("access")
            refresh_token = response.data.get("refresh")
            record_login_attempt(request, email, True, user=user)

            if user and access_token and refresh_token:
                session = record_successful_session(
                    request,
                    user,
                    access_token,
                    refresh_token,
                )
                response.data["session_id"] = session.SessionID

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
                response.data["user"] = {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "must_change_password": user.must_change_password,
                    "application": application.Code,
                }
        else:
            record_login_attempt(
                request,
                email,
                False,
                "invalid_credentials",
                user=user,
            )
        return response


class ApplicationScopedUserViewSet(CustomUserViewSet):
    def _application_user_from_uid(self, request):
        application = resolve_application_context(request)
        uid = request.data.get("uid")
        if not uid:
            return application, None
        try:
            user_id = decode_uid(uid)
        except Exception:
            return application, None
        User = get_user_model()
        user = User.objects.filter(pk=user_id).first()
        return application, user

    def activation(self, request, *args, **kwargs):
        application, user = self._application_user_from_uid(request)
        if user is not None and not account_belongs_to_application(user, application):
            return Response(
                {
                    "code": "APPLICATION_ACCESS_DENIED",
                    "detail": "Activation does not belong to this application.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().activation(request, *args, **kwargs)

    def resend_activation(self, request, *args, **kwargs):
        application = resolve_application_context(request)
        email = normalize_email(request.data.get("email"))
        user = find_local_account(application, email)

        if user is not None and not user.is_active:
            try:
                djoser_settings.EMAIL.activation(request, {"user": user}).send(
                    [get_user_email(user)]
                )
            except Exception:
                # Delivery failures are recorded by the email owner. Keep the
                # public response generic to avoid account enumeration.
                pass
            else:
                record_access_event(
                    request,
                    "identity.activation.resent",
                    user=user,
                    application=application,
                )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def reset_password(self, request, *args, **kwargs):
        application = resolve_application_context(request)
        email = normalize_email(request.data.get("email"))
        user = find_local_account(application, email, active_only=True)

        if user is not None:
            try:
                djoser_settings.EMAIL.password_reset(request, {"user": user}).send(
                    [get_user_email(user)]
                )
            except Exception:
                # Internal failure stays observable in EmailDeliveryLogs while
                # the public contract remains anti-enumeration safe.
                pass
            else:
                record_access_event(
                    request,
                    "identity.password.reset.requested",
                    user=user,
                    application=application,
                    metadata={
                        "first_access": bool(
                            user.must_change_password and not user.has_usable_password()
                        )
                    },
                )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def reset_password_confirm(self, request, *args, **kwargs):
        application = resolve_application_context(request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user

        if not account_belongs_to_application(user, application):
            return Response(
                {
                    "code": "APPLICATION_ACCESS_DENIED",
                    "detail": "Password reset does not belong to this application.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        user.set_password(serializer.data["new_password"])
        user.must_change_password = False
        if hasattr(user, "last_login"):
            user.last_login = now()
        user.save()

        record_access_event(
            request,
            "identity.password.reset.confirmed",
            user=user,
            application=application,
            metadata={"must_change_password": False},
        )

        if djoser_settings.PASSWORD_CHANGED_EMAIL_CONFIRMATION:
            context = {"user": user}
            to = [get_user_email(user)]
            djoser_settings.EMAIL.password_changed_confirmation(request, context).send(to)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def set_username(self, request, *args, **kwargs):
        application = resolve_application_context(request)
        if not account_belongs_to_application(request.user, application):
            return Response(
                {
                    "code": "APPLICATION_ACCESS_DENIED",
                    "detail": "Email change does not belong to this application.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        response = super().set_username(request, *args, **kwargs)
        if response.status_code == status.HTTP_204_NO_CONTENT:
            record_access_event(
                request,
                "identity.email.changed",
                user=request.user,
                application=application,
            )
        return response

    def reset_username(self, request, *args, **kwargs):
        application = resolve_application_context(request)
        email = normalize_email(request.data.get("email"))
        user = find_local_account(application, email, active_only=True)

        if user is not None:
            try:
                djoser_settings.EMAIL.username_reset(request, {"user": user}).send(
                    [get_user_email(user)]
                )
            except Exception:
                pass
            else:
                record_access_event(
                    request,
                    "identity.email.reset.requested",
                    user=user,
                    application=application,
                )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def reset_username_confirm(self, request, *args, **kwargs):
        application = resolve_application_context(request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user

        if not account_belongs_to_application(user, application):
            return Response(
                {
                    "code": "APPLICATION_ACCESS_DENIED",
                    "detail": "Email reset does not belong to this application.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        User = get_user_model()
        field_name = User.USERNAME_FIELD
        new_value = serializer.data["new_" + field_name]
        if field_name == "email":
            new_value = normalize_email(new_value)
        setattr(user, field_name, new_value)
        if hasattr(user, "last_login"):
            user.last_login = now()
        user.save()

        record_access_event(
            request,
            "identity.email.reset.confirmed",
            user=user,
            application=application,
        )

        if djoser_settings.USERNAME_CHANGED_EMAIL_CONFIRMATION:
            context = {"user": user}
            to = [get_user_email(user)]
            djoser_settings.EMAIL.username_changed_confirmation(request, context).send(to)
        return Response(status=status.HTTP_204_NO_CONTENT)
