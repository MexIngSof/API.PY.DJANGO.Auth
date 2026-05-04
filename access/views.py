from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from roles.models import Roles
from access.models import Permissions, UserPermissions, Modules
from .serializers import ModuleSerializer, RoleSerializer


class MePermissionsViewSet(viewsets.ViewSet):
    """
    /api/me/permissions/
    Devuelve roles, módulos autorizados y permisos efectivos.
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="permissions")
    def list_permissions(self, request):
        user = request.user

        # 1️⃣ Roles del usuario
        roles = Roles.objects.filter(
            userroles__UserID=user
        ).distinct()

        # 2️⃣ Permisos otorgados por rol
        role_perms = Permissions.objects.filter(
            rolepermissions__RoleID__in=roles
        ).select_related("ModuleID", "ActionID").distinct()

        # 3️⃣ Permisos agregados o revocados al usuario
        user_perms = UserPermissions.objects.filter(
            UserID=user
        ).select_related("PermissionID")

        # 4️⃣ Resolver permisos finales allow=True/False
        effective_perms = {}

        # Permisos heredados del rol
        for perm in role_perms:
            effective_perms[perm.Code] = True

        # Overrides por usuario
        for up in user_perms:
            effective_perms[up.PermissionID.Code] = up.Allow

        # 5️⃣ Identificar módulos permitidos con algún permiso allow=True
        module_ids = set(
            perm.ModuleID_id
            for perm in role_perms
            if perm.ModuleID_id is not None and effective_perms.get(perm.Code, False)
        )

        modules = Modules.objects.filter(
            ModuleID__in=module_ids
        ).order_by("ModuleID")

        # 6️⃣ JSON final
        data = {
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": f"{user.first_name} {user.last_name}",
            },
            "roles": RoleSerializer(roles, many=True).data,
            "modules": ModuleSerializer(modules, many=True).data,
            "permissions": [
                {"code": code, "allow": allow}
                for code, allow in effective_perms.items()
            ],
        }

        return Response(data)
