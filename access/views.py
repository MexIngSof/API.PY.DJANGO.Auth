from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import mixins, status, viewsets
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
    IdentityUserSerializer,
    ApplicationSerializer,
    LoginAttemptSerializer,
    MfaMethodSerializer,
    ModuleSerializer,
    OwnUserSessionSerializer,
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
from roles.models import Roles, UserRoles


def get_application_code(request):
    return (
        request.query_params.get("application_code")
        or request.query_params.get("ApplicationCode")
        or request.headers.get("X-Application-Code")
        or ""
    ).strip().upper()


def get_admin_application_filter(request):
    return (
        request.query_params.get("application_code")
        or request.query_params.get("ApplicationCode")
        or ""
    ).strip().upper()


def get_current_session(request):
    refresh_hash = request.COOKIES.get("refresh")
    if not refresh_hash:
        return None
    import hashlib

    token_hash = hashlib.sha256(refresh_hash.encode("utf-8")).hexdigest()
    return (
        UserSessions.objects.filter(
            UserID=request.user,
            RefreshTokenHash=token_hash,
            RevokedAt__isnull=True,
        )
        .order_by("-LastActivityAt")
        .first()
    )


def audit_session_event(request, event_type, session=None, metadata=None):
    application = None
    application_code = get_application_code(request)
    if application_code:
        application = Applications.objects.filter(Code=application_code, IsActive=True).first()

    AccessAuditEvents.objects.create(
        UserID=request.user,
        ApplicationID=application,
        EventType=event_type,
        IpAddress=request.META.get("REMOTE_ADDR"),
        UserAgent=request.META.get("HTTP_USER_AGENT", ""),
        Metadata={
            "session_id": getattr(session, "SessionID", None),
            "application_code": application_code,
            **(metadata or {}),
        },
    )


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

    def get_queryset(self):
        queryset = super().get_queryset()
        application_code = get_admin_application_filter(self.request)
        if application_code:
            queryset = queryset.filter(
                applicationroles__ApplicationID__Code=application_code,
                applicationroles__ApplicationID__IsActive=True,
            )
        return queryset.distinct().order_by("Name")

    @action(detail=True, methods=["patch"], url_path="permissions")
    def set_permissions(self, request, pk=None):
        role = self.get_object()
        permission_ids = request.data.get("permission_ids") or request.data.get("PermissionIds")
        permission_codes = request.data.get("permission_codes") or request.data.get("PermissionCodes")

        permissions = Permissions.objects.none()
        if permission_ids is not None:
            permissions = Permissions.objects.filter(PermissionID__in=permission_ids)
        elif permission_codes is not None:
            permissions = Permissions.objects.filter(Code__in=permission_codes)
        else:
            return Response(
                {"detail": "permission_ids or permission_codes is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        RolePermissions.objects.filter(RoleID=role).delete()
        for permission in permissions:
            RolePermissions.objects.get_or_create(RoleID=role, PermissionID=permission)

        AccessAuditEvents.objects.create(
            UserID=request.user,
            EventType="identity.role.permissions.updated",
            Metadata={
                "role_id": role.RoleID,
                "role_name": role.Name,
                "permission_codes": list(permissions.values_list("Code", flat=True)),
            },
        )
        return Response(RoleSerializer(role).data)


class PermissionViewSet(AdminModelViewSet):
    queryset = Permissions.objects.select_related("ModuleID", "ActionID").all().order_by("Code")
    serializer_class = PermissionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        application_code = get_admin_application_filter(self.request)
        if application_code:
            queryset = queryset.filter(
                applicationpermissions__ApplicationID__Code=application_code,
                applicationpermissions__ApplicationID__IsActive=True,
            )
        return queryset.distinct().order_by("Code")


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


class OwnUserSessionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    serializer_class = OwnUserSessionSerializer
    lookup_url_kwarg = "session_id"

    def get_queryset(self):
        queryset = UserSessions.objects.select_related(
            "DeviceID",
            "ApplicationID",
        ).filter(UserID=self.request.user).order_by("-LastActivityAt")
        application_code = get_application_code(self.request)
        if application_code:
            queryset = queryset.filter(ApplicationID__Code=application_code)
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        current_session = get_current_session(self.request)
        context["current_session_id"] = (
            current_session.SessionID if current_session is not None else None
        )
        return context

    def destroy(self, request, *args, **kwargs):
        session = self.get_object()
        now_value = timezone.now()
        session.RevokedAt = now_value
        session.RevokedReason = "USER_REVOKED"
        session.IsOnline = False
        session.save(update_fields=["RevokedAt", "RevokedReason", "IsOnline"])
        RefreshTokens.objects.filter(
            UserID=request.user,
            SessionID=session,
            RevokedAt__isnull=True,
        ).update(RevokedAt=now_value, RevokedReason="USER_REVOKED")
        audit_session_event(request, "identity.session.revoked", session=session)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"], url_path="revoke-all")
    def revoke_all(self, request):
        keep_current = bool(request.data.get("keep_current", False))
        current_session = get_current_session(request)
        queryset = self.get_queryset().filter(RevokedAt__isnull=True)
        if keep_current and current_session is not None:
            queryset = queryset.exclude(SessionID=current_session.SessionID)

        session_ids = list(queryset.values_list("SessionID", flat=True))
        now_value = timezone.now()
        updated = queryset.update(
            RevokedAt=now_value,
            RevokedReason="USER_REVOKED_ALL",
            IsOnline=False,
        )
        refresh_query = RefreshTokens.objects.filter(
            UserID=request.user,
            SessionID_id__in=session_ids,
            RevokedAt__isnull=True,
        )
        refresh_updated = refresh_query.update(
            RevokedAt=now_value,
            RevokedReason="USER_REVOKED_ALL",
        )
        audit_session_event(
            request,
            "identity.sessions.revoked_all",
            session=current_session,
            metadata={
                "keep_current": keep_current,
                "revoked_sessions": updated,
                "revoked_refresh_tokens": refresh_updated,
            },
        )
        return Response(
            {
                "revoked_sessions": updated,
                "revoked_refresh_tokens": refresh_updated,
                "kept_current": keep_current and current_session is not None,
            }
        )


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


class IdentityUserViewSet(AdminModelViewSet):
    serializer_class = IdentityUserSerializer

    def get_queryset(self):
        User = get_user_model()
        queryset = User.objects.all().order_by("email")
        application_code = get_admin_application_filter(self.request)
        search = (
            self.request.query_params.get("search")
            or self.request.query_params.get("q")
            or ""
        ).strip()

        if application_code:
            application = Applications.objects.filter(
                Code=application_code,
                IsActive=True,
            ).first()
            if application is None:
                return queryset.none()
            queryset = queryset.filter(idApp=application.ApplicationID)

        if search:
            queryset = queryset.filter(email__icontains=search)

        return queryset

    @action(detail=True, methods=["post"], url_path="roles")
    def assign_role(self, request, pk=None):
        user = self.get_object()
        role_id = request.data.get("role_id") or request.data.get("RoleId")
        role_name = request.data.get("role_name") or request.data.get("RoleName")

        role = None
        if role_id:
            role = Roles.objects.filter(RoleID=role_id).first()
        elif role_name:
            role = Roles.objects.filter(Name=str(role_name).strip()).first()

        if role is None:
            return Response({"detail": "Role not found."}, status=status.HTTP_404_NOT_FOUND)

        application_code = get_admin_application_filter(request)
        if application_code:
            allowed = ApplicationRoles.objects.filter(
                ApplicationID__Code=application_code,
                ApplicationID__IsActive=True,
                RoleID=role,
            ).exists()
            if not allowed:
                return Response(
                    {"detail": "Role is not registered for this application."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        UserRoles.objects.get_or_create(UserID=user, RoleID=role)
        AccessAuditEvents.objects.create(
            UserID=request.user,
            EventType="identity.user.role.assigned",
            Metadata={
                "target_user_id": user.id,
                "target_user_email": user.email,
                "role_id": role.RoleID,
                "role_name": role.Name,
                "application_code": application_code,
            },
        )
        return Response(self.get_serializer(user).data)

    @action(detail=True, methods=["delete"], url_path=r"roles/(?P<role_id>[^/.]+)")
    def remove_role(self, request, pk=None, role_id=None):
        user = self.get_object()
        deleted, _ = UserRoles.objects.filter(UserID=user, RoleID_id=role_id).delete()
        AccessAuditEvents.objects.create(
            UserID=request.user,
            EventType="identity.user.role.removed",
            Metadata={
                "target_user_id": user.id,
                "target_user_email": user.email,
                "role_id": role_id,
                "deleted": deleted,
                "application_code": get_admin_application_filter(request),
            },
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="permissions")
    def assign_permission(self, request, pk=None):
        user = self.get_object()
        permission_id = request.data.get("permission_id") or request.data.get("PermissionId")
        permission_code = request.data.get("permission_code") or request.data.get("PermissionCode")
        allow = request.data.get("allow", request.data.get("Allow", True))
        reason = request.data.get("reason") or request.data.get("Reason") or "Asignado desde JobCron."

        permission = None
        if permission_id:
            permission = Permissions.objects.filter(PermissionID=permission_id).first()
        elif permission_code:
            permission = Permissions.objects.filter(Code=str(permission_code).strip()).first()

        if permission is None:
            return Response({"detail": "Permission not found."}, status=status.HTTP_404_NOT_FOUND)

        application_code = get_admin_application_filter(request)
        if application_code:
            allowed = ApplicationPermissions.objects.filter(
                ApplicationID__Code=application_code,
                ApplicationID__IsActive=True,
                PermissionID=permission,
            ).exists()
            if not allowed:
                return Response(
                    {"detail": "Permission is not registered for this application."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        user_permission, _ = UserPermissions.objects.update_or_create(
            UserID=user,
            PermissionID=permission,
            defaults={"Allow": bool(allow), "Reason": reason},
        )
        AccessAuditEvents.objects.create(
            UserID=request.user,
            EventType="identity.user.permission.updated",
            Metadata={
                "target_user_id": user.id,
                "target_user_email": user.email,
                "permission_id": permission.PermissionID,
                "permission_code": permission.Code,
                "allow": user_permission.Allow,
                "application_code": application_code,
            },
        )
        return Response(self.get_serializer(user).data)

    @action(detail=True, methods=["delete"], url_path=r"permissions/(?P<permission_id>[^/.]+)")
    def remove_permission(self, request, pk=None, permission_id=None):
        user = self.get_object()
        deleted, _ = UserPermissions.objects.filter(
            UserID=user,
            PermissionID_id=permission_id,
        ).delete()
        AccessAuditEvents.objects.create(
            UserID=request.user,
            EventType="identity.user.permission.removed",
            Metadata={
                "target_user_id": user.id,
                "target_user_email": user.email,
                "permission_id": permission_id,
                "deleted": deleted,
                "application_code": get_admin_application_filter(request),
            },
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


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
