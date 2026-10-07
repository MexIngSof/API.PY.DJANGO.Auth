from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from access.application_admin_scope import ADMIN_TARGET_QUERY_KEYS, resolve_admin_target_application
from access.models import (
    AccessAuditEvents,
    ApplicationPermissions,
    ApplicationRoles,
    Permissions,
    UserPermissions,
)
from access.serializers import IdentityUserSerializer, PermissionSerializer, RoleSerializer
from roles.models import Roles, UserRoles


class ScopedAdminModelViewSet(ModelViewSet):
    permission_classes = [IsAdminUser]
    trusted_application_target_query_keys = ADMIN_TARGET_QUERY_KEYS

    def get_target_application(self):
        target = getattr(self, "_target_application", None)
        if target is None:
            target = resolve_admin_target_application(self.request)
            self._target_application = target
        return target


class ApplicationScopedRoleViewSet(ScopedAdminModelViewSet):
    serializer_class = RoleSerializer

    def get_queryset(self):
        target = self.get_target_application()
        return Roles.objects.filter(
            applicationroles__ApplicationID=target,
        ).distinct().order_by("Name")


class ApplicationScopedPermissionViewSet(ScopedAdminModelViewSet):
    serializer_class = PermissionSerializer

    def get_queryset(self):
        target = self.get_target_application()
        return Permissions.objects.select_related("ModuleID", "ActionID").filter(
            applicationpermissions__ApplicationID=target,
        ).distinct().order_by("Code")


class ApplicationScopedIdentityUserViewSet(ScopedAdminModelViewSet):
    serializer_class = IdentityUserSerializer

    def get_queryset(self):
        target = self.get_target_application()
        queryset = get_user_model().objects.filter(
            idApp=target.ApplicationID,
        ).order_by("email")
        search = (self.request.query_params.get("search") or self.request.query_params.get("q") or "").strip()
        if search:
            queryset = queryset.filter(email__icontains=search)
        return queryset

    @action(detail=True, methods=["post"], url_path="roles")
    def assign_role(self, request, pk=None):
        user = self.get_object()
        target = self.get_target_application()
        role_id = request.data.get("role_id") or request.data.get("RoleId")
        role_name = request.data.get("role_name") or request.data.get("RoleName")
        role = None
        if role_id:
            role = Roles.objects.filter(RoleID=role_id).first()
        elif role_name:
            role = Roles.objects.filter(Name=str(role_name).strip()).first()
        if role is None:
            return Response({"detail": "Role not found."}, status=status.HTTP_404_NOT_FOUND)
        if not ApplicationRoles.objects.filter(ApplicationID=target, RoleID=role).exists():
            return Response({"detail": "Role is not registered for this application."}, status=status.HTTP_400_BAD_REQUEST)
        UserRoles.objects.get_or_create(UserID=user, RoleID=role)
        self._audit(request, "identity.user.role.assigned", user, target, role_id=role.RoleID, role_name=role.Name)
        return Response(self.get_serializer(user).data)

    @action(detail=True, methods=["delete"], url_path=r"roles/(?P<role_id>[^/.]+)")
    def remove_role(self, request, pk=None, role_id=None):
        user = self.get_object()
        target = self.get_target_application()
        if not ApplicationRoles.objects.filter(ApplicationID=target, RoleID_id=role_id).exists():
            return Response({"detail": "Role is not registered for this application."}, status=status.HTTP_400_BAD_REQUEST)
        deleted, _ = UserRoles.objects.filter(UserID=user, RoleID_id=role_id).delete()
        self._audit(request, "identity.user.role.removed", user, target, role_id=role_id, deleted=deleted)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="permissions")
    def assign_permission(self, request, pk=None):
        user = self.get_object()
        target = self.get_target_application()
        permission_id = request.data.get("permission_id") or request.data.get("PermissionId")
        permission_code = request.data.get("permission_code") or request.data.get("PermissionCode")
        permission = None
        if permission_id:
            permission = Permissions.objects.filter(PermissionID=permission_id).first()
        elif permission_code:
            permission = Permissions.objects.filter(Code=str(permission_code).strip()).first()
        if permission is None:
            return Response({"detail": "Permission not found."}, status=status.HTTP_404_NOT_FOUND)
        if not ApplicationPermissions.objects.filter(ApplicationID=target, PermissionID=permission).exists():
            return Response({"detail": "Permission is not registered for this application."}, status=status.HTTP_400_BAD_REQUEST)
        allow = request.data.get("allow", request.data.get("Allow", True))
        reason = request.data.get("reason") or request.data.get("Reason") or "Application-scoped administration."
        user_permission, _ = UserPermissions.objects.update_or_create(
            UserID=user,
            PermissionID=permission,
            defaults={"Allow": bool(allow), "Reason": reason},
        )
        self._audit(
            request,
            "identity.user.permission.updated",
            user,
            target,
            permission_id=permission.PermissionID,
            permission_code=permission.Code,
            allow=user_permission.Allow,
        )
        return Response(self.get_serializer(user).data)

    @action(detail=True, methods=["delete"], url_path=r"permissions/(?P<permission_id>[^/.]+)")
    def remove_permission(self, request, pk=None, permission_id=None):
        user = self.get_object()
        target = self.get_target_application()
        if not ApplicationPermissions.objects.filter(ApplicationID=target, PermissionID_id=permission_id).exists():
            return Response({"detail": "Permission is not registered for this application."}, status=status.HTTP_400_BAD_REQUEST)
        deleted, _ = UserPermissions.objects.filter(UserID=user, PermissionID_id=permission_id).delete()
        self._audit(request, "identity.user.permission.removed", user, target, permission_id=permission_id, deleted=deleted)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def _audit(request, event_type, target_user, application, **metadata):
        AccessAuditEvents.objects.create(
            UserID=request.user,
            ApplicationID=application,
            EventType=event_type,
            Metadata={
                "target_user_id": target_user.id,
                "target_user_email": target_user.email,
                "application_code": application.Code,
                **metadata,
            },
        )
