from djoser.serializers import UserCreatePasswordRetypeSerializer
from rest_framework import serializers
from roles.models import Roles, UserRoles
from .models import UserAccount


class CustomUserCreatePasswordRetypeSerializer(UserCreatePasswordRetypeSerializer):

    role = serializers.CharField(write_only=True)

    class Meta(UserCreatePasswordRetypeSerializer.Meta):
        model = UserAccount
        fields = UserCreatePasswordRetypeSerializer.Meta.fields + (
            "first_name",
            "last_name",
            "role",
        )

    def validate(self, attrs):

        # EXTRAE Y GUARDA LOS CAMPOS PERSONALIZADOS
        role = attrs.pop("role", None)

        # VALIDA CON DJOSER (solo password, email, first_name, last_name)
        attrs = super().validate(attrs)

        # REINSERTA los campos personalizados dentro de validated_data
        attrs["role"] = role

        return attrs

    def create(self, validated_data):

        # QUITAR re_password
        validated_data.pop("re_password", None)

        # Extraer campos personalizados
        role_name = validated_data.pop("role")

        # Crear usuario con Djoser
        user = super().create(validated_data)

        # Guardar idApp
        user.save()

        # Asignar rol
        role_obj = Roles.objects.get(Name=role_name)
        UserRoles.objects.create(UserID=user, RoleID=role_obj)

        return user
