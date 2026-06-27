from djoser.serializers import UserCreatePasswordRetypeSerializer
from rest_framework import serializers

from access.models import Applications, PasswordHistory
from roles.models import Roles, UserRoles
from user.models import UserAccount


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

    def validate_role(self, value):
        if not value:
            return value
        if not Roles.objects.filter(Name=value).exists():
            raise serializers.ValidationError("Role does not exist.")
        return value

    def validate_ApplicationCode(self, value):
        application_code = (value or "").strip().upper()
        if application_code and not Applications.objects.filter(
            Code=application_code,
            IsActive=True,
        ).exists():
            raise serializers.ValidationError("ApplicationCode does not exist or is inactive.")
        return application_code

    def validate(self, attrs):
        role = attrs.pop("role", None)
        application_code = attrs.pop("ApplicationCode", "")
        request = self.context.get("request")
        if not application_code and request is not None:
            application_code = (
                request.headers.get("X-Application-Code")
                or request.data.get("application_code")
                or request.query_params.get("application_code")
                or ""
            )

        if application_code:
            application = Applications.objects.filter(
                Code=application_code.strip().upper(),
                IsActive=True,
            ).first()
            if application is not None and not attrs.get("idApp"):
                attrs["idApp"] = application.ApplicationID

        if application_code.strip().upper() == "LEXNOVA":
            role = "CLIENT_BASE"
        elif application_code.strip().upper() == "REFAPART":
            role = "CUSTOMER"
        elif not role:
            raise serializers.ValidationError({"role": "This field is required."})

        attrs = super().validate(attrs)
        attrs["role"] = role
        attrs["ApplicationCode"] = application_code
        return attrs

    def create(self, validated_data):
        validated_data.pop("re_password", None)
        role_name = validated_data.pop("role")
        validated_data.pop("ApplicationCode", "")

        user = super().create(validated_data)
        role_obj = Roles.objects.get(Name=role_name)
        UserRoles.objects.create(UserID=user, RoleID=role_obj)
        PasswordHistory.objects.create(UserID=user, PasswordHash=user.password)

        return user
