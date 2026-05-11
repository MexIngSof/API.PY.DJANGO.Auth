from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from access.models import (
    AccessAuditEvents,
    Actions,
    ApplicationPermissions,
    ApplicationRoles,
    Applications,
    LoginAttempts,
    MfaMethods,
    Modules,
    PasswordHistory,
    Permissions,
    RecoveryCodes,
    RefreshTokens,
    RolePermissions,
    SocialLoginAttempts,
    SocialProviders,
    UserSocialAccounts,
    UserDevices,
    UserPermissions,
    UserSessions,
)
from access.serializers import (
    AccessAuditEventSerializer,
    ActionSerializer,
    ApplicationPermissionSerializer,
    ApplicationRoleSerializer,
    ApplicationSerializer,
    LoginAttemptSerializer,
    MfaMethodSerializer,
    ModuleSerializer,
    PasswordHistorySerializer,
    PermissionSerializer,
    RecoveryCodeSerializer,
    RefreshTokenSerializer,
    RolePermissionSerializer,
    RoleSerializer,
    SocialLoginAttemptSerializer,
    SocialProviderSerializer,
    UserSocialAccountSerializer,
    UserDeviceSerializer,
    UserPermissionSerializer,
    UserSessionSerializer,
)
from roles.models import Roles


def get_application_code(request):
    return (
        request.query_params.get("application_code")
        or request.query_params.get("ApplicationCode")
        or request.headers.get("X-Application-Code")
        or ""
    ).strip().upper()


class AdminModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]


class ApplicationViewSet(AdminModelViewSet):
    queryset = Applications.objects.all().order_by("Code")
    serializer_class = ApplicationSerializer


class SocialProviderViewSet(AdminModelViewSet):
    queryset = SocialProviders.objects.all().order_by("Code")
    serializer_class = SocialProviderSerializer


class UserSocialAccountViewSet(AdminModelViewSet):
    queryset = UserSocialAccounts.objects.select_related(
        "UserID",
        "SocialProviderID",
    ).all().order_by("-LastLoginAt", "-UpdatedAt")
    serializer_class = UserSocialAccountSerializer


class SocialLoginAttemptViewSet(AdminModelViewSet):
    queryset = SocialLoginAttempts.objects.select_related(
        "UserID",
        "SocialProviderID",
    ).all().order_by("-CreatedAt")
    serializer_class = SocialLoginAttemptSerializer


class ModuleViewSet(AdminModelViewSet):
    queryset = Modules.objects.all().order_by("Code")
    serializer_class = ModuleSerializer


class ActionViewSet(AdminModelViewSet):
    queryset = Actions.objects.all().order_by("Name")
    serializer_class = ActionSerializer


class RoleViewSet(AdminModelViewSet):
    queryset = Roles.objects.all().order_by("Name")
    serializer_class = RoleSerializer


class PermissionViewSet(AdminModelViewSet):
    queryset = Permissions.objects.select_related("ModuleID", "ActionID").all().order_by("Code")
    serializer_class = PermissionSerializer


class RolePermissionViewSet(AdminModelViewSet):
    queryset = RolePermissions.objects.select_related("RoleID", "PermissionID").all()
    serializer_class = RolePermissionSerializer


class UserPermissionViewSet(AdminModelViewSet):
    queryset = UserPermissions.objects.select_related("UserID", "PermissionID").all()
    serializer_class = UserPermissionSerializer


class ApplicationRoleViewSet(AdminModelViewSet):
    queryset = ApplicationRoles.objects.select_related("ApplicationID", "RoleID").all()
    serializer_class = ApplicationRoleSerializer


class ApplicationPermissionViewSet(AdminModelViewSet):
    queryset = ApplicationPermissions.objects.select_related("ApplicationID", "PermissionID").all()
    serializer_class = ApplicationPermissionSerializer


class UserDeviceViewSet(AdminModelViewSet):
    queryset = UserDevices.objects.select_related("UserID").all().order_by("-LastSeenAt")
    serializer_class = UserDeviceSerializer


class UserSessionViewSet(AdminModelViewSet):
    queryset = UserSessions.objects.select_related("UserID", "DeviceID", "ApplicationID").all().order_by("-LastActivityAt")
    serializer_class = UserSessionSerializer


class RefreshTokenViewSet(AdminModelViewSet):
    queryset = RefreshTokens.objects.select_related("UserID", "SessionID").all().order_by("-CreatedAt")
    serializer_class = RefreshTokenSerializer


class PasswordHistoryViewSet(AdminModelViewSet):
    queryset = PasswordHistory.objects.select_related("UserID").all().order_by("-CreatedAt")
    serializer_class = PasswordHistorySerializer


class LoginAttemptViewSet(AdminModelViewSet):
    queryset = LoginAttempts.objects.select_related("UserID").all().order_by("-CreatedAt")
    serializer_class = LoginAttemptSerializer


class MfaMethodViewSet(AdminModelViewSet):
    queryset = MfaMethods.objects.select_related("UserID").all().order_by("UserID", "MethodType")
    serializer_class = MfaMethodSerializer


class RecoveryCodeViewSet(AdminModelViewSet):
    queryset = RecoveryCodes.objects.select_related("UserID").all().order_by("-CreatedAt")
    serializer_class = RecoveryCodeSerializer


class AccessAuditEventViewSet(AdminModelViewSet):
    queryset = AccessAuditEvents.objects.select_related("UserID", "ApplicationID").all().order_by("-CreatedAt")
    serializer_class = AccessAuditEventSerializer


class MePermissionsViewSet(viewsets.ViewSet):
    """
    /api/access/me/permissions/
    Returns effective roles, modules and permissions for the current user.
    Optional filters:
    - ?application_code=TECNOTELEC
    - X-Application-Code: TECNOTELEC
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="permissions")
    def list_permissions(self, request):
        user = request.user
        application_code = get_application_code(request)
        application = None

        roles = Roles.objects.filter(userroles__UserID=user).distinct()

        if application_code:
            application = Applications.objects.filter(
                Code=application_code,
                IsActive=True,
            ).first()

        if application is not None:
            app_roles = roles.filter(applicationroles__ApplicationID=application)
            if app_roles.exists():
                roles = app_roles

        role_perms = Permissions.objects.filter(
            rolepermissions__RoleID__in=roles
        ).select_related("ModuleID", "ActionID").distinct()

        if application is not None:
            app_permission_ids = ApplicationPermissions.objects.filter(
                ApplicationID=application,
            ).values_list("PermissionID_id", flat=True)
            if app_permission_ids.exists():
                role_perms = role_perms.filter(PermissionID__in=app_permission_ids)

        user_perms = UserPermissions.objects.filter(
            UserID=user
        ).select_related("PermissionID", "PermissionID__ModuleID")

        effective_perms = {perm.Code: True for perm in role_perms}

        for user_perm in user_perms:
            code = user_perm.PermissionID.Code
            if application is None or effective_perms.get(code) is not None:
                effective_perms[code] = user_perm.Allow

        role_module_ids = {
            perm.ModuleID_id
            for perm in role_perms
            if perm.ModuleID_id is not None and effective_perms.get(perm.Code, False)
        }
        user_module_ids = {
            user_perm.PermissionID.ModuleID_id
            for user_perm in user_perms
            if user_perm.PermissionID.ModuleID_id is not None
            and effective_perms.get(user_perm.PermissionID.Code, False)
        }

        modules = Modules.objects.filter(
            ModuleID__in=role_module_ids | user_module_ids
        ).order_by("ModuleID")

        data = {
            "application": application.Code if application is not None else application_code,
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

        return Response(data)
