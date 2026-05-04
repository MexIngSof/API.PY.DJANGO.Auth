from rest_framework import serializers
from roles.models import Roles
from access.models import Modules, Permissions


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modules
        fields = [
            "ModuleID",
            "Name",
            "Description",
            "Code",    # 🔥 NECESARIO
            "Path",    # 🔥 NECESARIO
        ]


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = ["RoleID", "Name", "Description"]


class PermissionSerializer(serializers.ModelSerializer):
    module = ModuleSerializer(source="ModuleID")
    action_name = serializers.CharField(source="ActionID.Name")

    class Meta:
        model = Permissions
        fields = [
            "PermissionID",
            "Code",
            "module",
            "action_name",
        ]
