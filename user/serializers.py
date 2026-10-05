from djoser.serializers import UserCreatePasswordRetypeSerializer
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from access.models import ApplicationRoles, PasswordHistory
from roles.models import Roles, UserRoles
from user.account_scope import find_local_account, normalize_email
from user.application_scope import resolve_application_context
from user.models import UserAccount


REGISTRATION_ROLE_BY_APPLICATION = {
    "LEXNOVA": "CLIENT_BASE",
    "REFAPART": "CUSTOMER",
}


class ApplicationScopedTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        request = self.context.get("request")
        if request is None:
            raise AuthenticationFailed(
                "Application context is required.",
                code="APPLICATION_CODE_REQUIRED",
            )

        application = resolve_application_context(request)
        email = normalize_email(attrs.get("email"))
        password = attrs.get("password") or ""
        user = find_local_account(application, email)

        if (
            user is None
            or not getattr(user, "is_active", False)
            or not user.check_password(password)
        ):
            raise AuthenticationFailed(
                "No active account found with the given credentials.",
                code="no_active_account",
            )

        self.user = user
        refresh = self.get_token(user)
        refresh["application_id"] = int(application.ApplicationID)
        refresh["application_code"] = application.Code
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }


class CustomUserCreatePasswordRetypeSerializer(UserCreatePasswordRetypeSerializer):
    idApp = serializers.IntegerField(required=False)
    role = serializers.CharField(write_only=True, required=False, allow_blank=True)
    ApplicationCode = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta(UserCreatePasswordRetypeSerializer.Meta):
        model = UserAccount
        fields = UserCreatePasswordRetypeSerializer.Meta.fields + (
            "first_name",
            "last_name",
            "idApp",
            "role",
            "ApplicationCode",
        )

    def validate(self, attrs):
        request = self.context.get("request")
        if request is None:
            raise serializers.ValidationError(
                {"detail": "Application context is required."}
            )

        application = resolve_application_context(request)
        role_name = REGISTRATION_ROLE_BY_APPLICATION.get(application.Code)
        if not role_name:
            raise serializers.ValidationError(
                {"detail": "Registration is not enabled for this application."}
            )

        role_obj = Roles.objects.filter(Name=role_name).first()
        if role_obj is None or not ApplicationRoles.objects.filter(
            ApplicationID=application,
            RoleID=role_obj,
        ).exists():
            raise serializers.ValidationError(
                {"detail": "Registration role is not configured for this application."}
            )

        # Client-provided application/role fields are compatibility inputs only.
        # The trusted Gateway context is authoritative.
        attrs["idApp"] = application.ApplicationID
        attrs.pop("role", None)
        attrs.pop("ApplicationCode", None)

        attrs = super().validate(attrs)
        attrs["role"] = role_name
        return attrs

    def create(self, validated_data):
        validated_data.pop("re_password", None)
        role_name = validated_data.pop("role")
        validated_data.pop("ApplicationCode", None)

        user = super().create(validated_data)
        role_obj = Roles.objects.get(Name=role_name)
        UserRoles.objects.create(UserID=user, RoleID=role_obj)
        PasswordHistory.objects.create(UserID=user, PasswordHash=user.password)

        return user
