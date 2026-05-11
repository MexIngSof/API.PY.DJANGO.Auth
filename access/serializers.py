from rest_framework import serializers

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
        fields = ["RoleID", "Name", "Description", "CreatedAt", "UpdatedAt"]
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
