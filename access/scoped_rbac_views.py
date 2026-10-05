from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from access.models import (
    ApplicationPermissions,
    ApplicationRoles,
    Modules,
    Permissions,
    UserPermissions,
)
from access.serializers import ModuleSerializer, RoleSerializer
from roles.models import Roles
from user.application_scope import resolve_application_context


class ApplicationScopedMePermissionsViewSet(viewsets.ViewSet):
    """Return effective RBAC only inside the trusted Gateway application."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="permissions")
    def list_permissions(self, request):
        user = request.user
        application = resolve_application_context(request)

        application_role_ids = ApplicationRoles.objects.filter(
            ApplicationID=application,
        ).values_list("RoleID_id", flat=True)
        roles = Roles.objects.filter(
            userroles__UserID=user,
            RoleID__in=application_role_ids,
        ).distinct()

        application_permission_ids = ApplicationPermissions.objects.filter(
            ApplicationID=application,
        ).values_list("PermissionID_id", flat=True)
        role_perms = Permissions.objects.filter(
            rolepermissions__RoleID__in=roles,
            PermissionID__in=application_permission_ids,
        ).select_related("ModuleID", "ActionID").distinct()

        user_perms = UserPermissions.objects.filter(
            UserID=user,
            PermissionID_id__in=application_permission_ids,
        ).select_related("PermissionID", "PermissionID__ModuleID")

        effective_perms = {permission.Code: True for permission in role_perms}
        for user_permission in user_perms:
            code = user_permission.PermissionID.Code
            if code in effective_perms:
                effective_perms[code] = user_permission.Allow

        role_module_ids = {
            permission.ModuleID_id
            for permission in role_perms
            if permission.ModuleID_id is not None
            and effective_perms.get(permission.Code, False)
        }
        user_module_ids = {
            user_permission.PermissionID.ModuleID_id
            for user_permission in user_perms
            if user_permission.PermissionID.ModuleID_id is not None
            and effective_perms.get(user_permission.PermissionID.Code, False)
        }
        modules = Modules.objects.filter(
            ModuleID__in=role_module_ids | user_module_ids
        ).order_by("ModuleID")

        return Response(
            {
                "application": application.Code,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "full_name": f"{user.first_name} {user.last_name}".strip(),
                },
                "roles": RoleSerializer(roles, many=True).data,
                "modules": ModuleSerializer(modules, many=True).data,
                "permissions": [
                    {"code": code, "allow": allow}
                    for code, allow in sorted(effective_perms.items())
                ],
            }
        )
