from rest_framework import serializers

from django.contrib.auth import get_user_model

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
from roles.models import Roles
from roles.models import UserRoles


class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Applications
        fields = [
            "ApplicationID",
            "Code",
            "Name",
            "Description",
            "IsActive",
            "CreatedAt",
            "UpdatedAt",
        ]
        read_only_fields = ["CreatedAt", "UpdatedAt"]


class SocialProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialProviders
        fields = [
            "SocialProviderID",
            "Code",
            "Name",
            "BackendName",
            "IsActive",
            "CreatedAt",
            "UpdatedAt",
        ]
        read_only_fields = ["CreatedAt", "UpdatedAt"]


class UserSocialAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSocialAccounts
        fields = [
            "UserSocialAccountID",
            "UserID",
            "SocialProviderID",
            "ProviderUserId",
            "Email",
            "DisplayName",
            "ProfileUrl",
            "AvatarUrl",
            "IsActive",
            "LastLoginAt",
            "CreatedAt",
            "UpdatedAt",
        ]
        read_only_fields = ["CreatedAt", "UpdatedAt"]


class SocialLoginAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialLoginAttempts
        fields = [
            "SocialLoginAttemptID",
            "UserID",
            "SocialProviderID",
            "ApplicationCode",
            "Email",
            "IpAddress",
            "UserAgent",
            "Success",
            "FailureReason",
            "CreatedAt",
        ]
        read_only_fields = fields


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modules
        fields = [
            "ModuleID",
            "Name",
            "Description",
            "Code",
            "Path",
            "CreatedAt",
            "UpdatedAt",
        ]
        read_only_fields = ["CreatedAt", "UpdatedAt"]


class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actions
        fields = ["ActionID", "Name", "Description", "CreatedAt", "UpdatedAt"]
        read_only_fields = ["CreatedAt", "UpdatedAt"]


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = ["RoleID", "Name", "DisplayName", "Description", "CreatedAt", "UpdatedAt"]
        read_only_fields = ["CreatedAt", "UpdatedAt"]


class PermissionSerializer(serializers.ModelSerializer):
    module = ModuleSerializer(source="ModuleID", read_only=True)
    action_name = serializers.CharField(source="ActionID.Name", read_only=True)

    class Meta:
        model = Permissions
        fields = [
            "PermissionID",
            "ModuleID",
            "ActionID",
            "Code",
            "module",
            "action_name",
            "CreatedAt",
            "UpdatedAt",
        ]
        read_only_fields = ["CreatedAt", "UpdatedAt"]


class RolePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolePermissions
        fields = ["id", "RoleID", "PermissionID", "CreatedAt", "UpdatedAt"]
        read_only_fields = ["CreatedAt", "UpdatedAt"]


class UserPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPermissions
        fields = [
            "id",
            "UserID",
            "PermissionID",
            "Allow",
            "Reason",
            "CreatedAt",
            "UpdatedAt",
        ]
        read_only_fields = ["CreatedAt", "UpdatedAt"]


class ApplicationRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationRoles
        fields = ["id", "ApplicationID", "RoleID", "CreatedAt", "UpdatedAt"]
        read_only_fields = ["CreatedAt", "UpdatedAt"]


class ApplicationPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationPermissions
        fields = ["id", "ApplicationID", "PermissionID", "CreatedAt", "UpdatedAt"]
        read_only_fields = ["CreatedAt", "UpdatedAt"]


class UserDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDevices
        fields = [
            "DeviceID",
            "UserID",
            "DeviceName",
            "DeviceType",
            "OperatingSystem",
            "Browser",
            "IpAddress",
            "UserAgent",
            "FingerprintHash",
            "IsTrusted",
            "IsActive",
            "LastSeenAt",
            "CreatedAt",
            "RevokedAt",
            "RevokedReason",
        ]
        read_only_fields = ["LastSeenAt", "CreatedAt"]
        extra_kwargs = {"FingerprintHash": {"write_only": True}}


class UserSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSessions
        fields = [
            "SessionID",
            "UserID",
            "DeviceID",
            "ApplicationID",
            "AccessTokenJti",
            "StartedAt",
            "LastActivityAt",
            "ExpiresAt",
            "RevokedAt",
            "RevokedReason",
            "IsOnline",
        ]
        read_only_fields = ["StartedAt", "LastActivityAt", "AccessTokenJti"]


class OwnUserSessionSerializer(serializers.ModelSerializer):
    application_code = serializers.CharField(source="ApplicationID.Code", read_only=True)
    application_name = serializers.CharField(source="ApplicationID.Name", read_only=True)
    device_name = serializers.CharField(source="DeviceID.DeviceName", read_only=True)
    device_type = serializers.CharField(source="DeviceID.DeviceType", read_only=True)
    browser = serializers.CharField(source="DeviceID.Browser", read_only=True)
    operating_system = serializers.CharField(source="DeviceID.OperatingSystem", read_only=True)
    ip_address = serializers.IPAddressField(source="DeviceID.IpAddress", read_only=True)
    is_current = serializers.SerializerMethodField()
    is_revoked = serializers.SerializerMethodField()

    class Meta:
        model = UserSessions
        fields = [
            "SessionID",
            "application_code",
            "application_name",
            "device_name",
            "device_type",
            "browser",
            "operating_system",
            "ip_address",
            "StartedAt",
            "LastActivityAt",
            "ExpiresAt",
            "RevokedAt",
            "RevokedReason",
            "IsOnline",
            "is_current",
            "is_revoked",
        ]
        read_only_fields = fields

    def get_is_current(self, obj):
        current_session_id = self.context.get("current_session_id")
        return bool(current_session_id and str(obj.SessionID) == str(current_session_id))

    def get_is_revoked(self, obj):
        return obj.RevokedAt is not None


class RefreshTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefreshTokens
        fields = [
            "RefreshTokenID",
            "UserID",
            "SessionID",
            "Jti",
            "ExpiresAt",
            "RevokedAt",
            "RevokedReason",
            "CreatedAt",
        ]
        read_only_fields = fields


class PasswordHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PasswordHistory
        fields = ["PasswordHistoryID", "UserID", "CreatedAt"]
        read_only_fields = fields


class LoginAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginAttempts
        fields = [
            "LoginAttemptID",
            "UserID",
            "Email",
            "ApplicationCode",
            "IpAddress",
            "UserAgent",
            "Success",
            "FailureReason",
            "CreatedAt",
        ]
        read_only_fields = fields


class MfaMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = MfaMethods
        fields = [
            "MfaMethodID",
            "UserID",
            "MethodType",
            "IsEnabled",
            "VerifiedAt",
            "CreatedAt",
            "UpdatedAt",
        ]
        read_only_fields = ["CreatedAt", "UpdatedAt"]


class RecoveryCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecoveryCodes
        fields = ["RecoveryCodeID", "UserID", "UsedAt", "CreatedAt"]
        read_only_fields = fields


class AccessAuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessAuditEvents
        fields = [
            "AccessAuditEventID",
            "UserID",
            "ApplicationID",
            "EventType",
            "IpAddress",
            "UserAgent",
            "Metadata",
            "CreatedAt",
        ]
        read_only_fields = fields


class IdentityUserSerializer(serializers.ModelSerializer):
    application = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()
    direct_permissions = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "is_superuser",
            "must_change_password",
            "idApp",
            "application",
            "roles",
            "direct_permissions",
        ]
        read_only_fields = ["email", "idApp", "application", "roles", "direct_permissions"]

    def get_application(self, obj):
        application = Applications.objects.filter(ApplicationID=obj.idApp).first()
        if application is None:
            return None
        return {
            "id": application.ApplicationID,
            "code": application.Code,
            "name": application.Name,
            "is_active": application.IsActive,
        }

    def get_roles(self, obj):
        roles = Roles.objects.filter(userroles__UserID=obj).order_by("Name")
        return [
            {
                "id": role.RoleID,
                "name": role.Name,
                "display_name": role.DisplayName or role.Name,
                "description": role.Description,
            }
            for role in roles
        ]

    def get_direct_permissions(self, obj):
        rows = UserPermissions.objects.filter(UserID=obj).select_related(
            "PermissionID",
            "PermissionID__ModuleID",
        ).order_by("PermissionID__Code")
        return [
            {
                "id": row.id,
                "permission_id": row.PermissionID_id,
                "code": row.PermissionID.Code,
                "module": row.PermissionID.ModuleID.Code if row.PermissionID.ModuleID_id else None,
                "allow": row.Allow,
                "reason": row.Reason,
            }
            for row in rows
        ]
