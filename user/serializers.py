from djoser.serializers import UserCreatePasswordRetypeSerializer
from rest_framework import serializers

from access.models import Applications, PasswordHistory
from roles.models import Roles, UserRoles
from user.models import UserAccount


class CustomUserCreatePasswordRetypeSerializer(UserCreatePasswordRetypeSerializer):
    role = serializers.CharField(write_only=True)
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
