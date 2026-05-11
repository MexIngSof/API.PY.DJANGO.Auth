from django.contrib import admin

from access.models import (
    AccessAuditEvents,
    Actions,
    ApplicationEmailSettings,
    ApplicationPermissions,
    ApplicationRoles,
    Applications,
    EmailDeliveryLogs,
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
    TransactionalEmailTemplates,
)


@admin.register(Applications)
class ApplicationsAdmin(admin.ModelAdmin):
    list_display = ("Code", "Name", "IsActive", "UpdatedAt")
    search_fields = ("Code", "Name")
    list_filter = ("IsActive",)


@admin.register(ApplicationEmailSettings)
class ApplicationEmailSettingsAdmin(admin.ModelAdmin):
    list_display = ("ApplicationID", "CommercialName", "SenderEmail", "IsActive", "UpdatedAt")
    list_filter = ("IsActive", "ApplicationID")
    search_fields = ("ApplicationID__Code", "CommercialName", "SenderEmail", "BaseDomain")


@admin.register(TransactionalEmailTemplates)
class TransactionalEmailTemplatesAdmin(admin.ModelAdmin):
    list_display = ("ApplicationID", "ActionCode", "LanguageCode", "Channel", "IsActive", "UpdatedAt")
    list_filter = ("ApplicationID", "ActionCode", "LanguageCode", "Channel", "IsActive")
    search_fields = ("ApplicationID__Code", "ActionCode", "SubjectTemplate")


@admin.register(EmailDeliveryLogs)
class EmailDeliveryLogsAdmin(admin.ModelAdmin):
    list_display = ("ActionCode", "ToEmail", "ApplicationID", "Status", "CreatedAt", "SentAt")
    list_filter = ("ActionCode", "Status", "ApplicationID")
    search_fields = ("ToEmail", "Subject", "ErrorMessage")
    readonly_fields = ("CreatedAt", "SentAt")


@admin.register(SocialProviders)
class SocialProvidersAdmin(admin.ModelAdmin):
    list_display = ("Code", "Name", "BackendName", "IsActive", "UpdatedAt")
    search_fields = ("Code", "Name", "BackendName")
    list_filter = ("IsActive",)


@admin.register(UserSocialAccounts)
class UserSocialAccountsAdmin(admin.ModelAdmin):
    list_display = ("UserID", "SocialProviderID", "ProviderUserId", "Email", "IsActive", "LastLoginAt")
    list_filter = ("SocialProviderID", "IsActive")
    search_fields = ("UserID__email", "ProviderUserId", "Email", "DisplayName")


@admin.register(SocialLoginAttempts)
class SocialLoginAttemptsAdmin(admin.ModelAdmin):
    list_display = ("SocialProviderID", "UserID", "Email", "ApplicationCode", "Success", "IpAddress", "CreatedAt")
    list_filter = ("SocialProviderID", "Success", "ApplicationCode")
    search_fields = ("UserID__email", "Email", "IpAddress", "FailureReason")
    readonly_fields = ("CreatedAt",)


@admin.register(Modules)
class ModulesAdmin(admin.ModelAdmin):
    list_display = ("Code", "Name", "Path")
    search_fields = ("Code", "Name", "Path")


@admin.register(Actions)
class ActionsAdmin(admin.ModelAdmin):
    list_display = ("Name", "Description")
    search_fields = ("Name",)


@admin.register(Permissions)
class PermissionsAdmin(admin.ModelAdmin):
    list_display = ("Code", "ModuleID", "ActionID")
    search_fields = ("Code", "ModuleID__Code", "ActionID__Name")
    list_filter = ("ModuleID", "ActionID")


@admin.register(ApplicationRoles)
class ApplicationRolesAdmin(admin.ModelAdmin):
    list_display = ("ApplicationID", "RoleID", "UpdatedAt")
    list_filter = ("ApplicationID", "RoleID")


@admin.register(ApplicationPermissions)
class ApplicationPermissionsAdmin(admin.ModelAdmin):
    list_display = ("ApplicationID", "PermissionID", "UpdatedAt")
    list_filter = ("ApplicationID", "PermissionID")


@admin.register(RolePermissions)
class RolePermissionsAdmin(admin.ModelAdmin):
    list_display = ("RoleID", "PermissionID", "UpdatedAt")
    list_filter = ("RoleID", "PermissionID")


@admin.register(UserPermissions)
class UserPermissionsAdmin(admin.ModelAdmin):
    list_display = ("UserID", "PermissionID", "Allow", "UpdatedAt")
    list_filter = ("Allow", "PermissionID")
    search_fields = ("UserID__email", "PermissionID__Code", "Reason")


@admin.register(UserDevices)
class UserDevicesAdmin(admin.ModelAdmin):
    list_display = ("UserID", "DeviceName", "IpAddress", "IsTrusted", "IsActive", "LastSeenAt")
    list_filter = ("IsTrusted", "IsActive")
    search_fields = ("UserID__email", "DeviceName", "FingerprintHash", "IpAddress")
    readonly_fields = ("FingerprintHash", "CreatedAt", "LastSeenAt")


@admin.register(UserSessions)
class UserSessionsAdmin(admin.ModelAdmin):
    list_display = ("UserID", "ApplicationID", "DeviceID", "IsOnline", "StartedAt", "RevokedAt")
    list_filter = ("ApplicationID", "IsOnline")
    search_fields = ("UserID__email", "AccessTokenJti")
    readonly_fields = ("AccessTokenJti", "RefreshTokenHash", "StartedAt", "LastActivityAt")


@admin.register(RefreshTokens)
class RefreshTokensAdmin(admin.ModelAdmin):
    list_display = ("UserID", "SessionID", "Jti", "ExpiresAt", "RevokedAt", "CreatedAt")
    search_fields = ("UserID__email", "Jti")
    readonly_fields = ("TokenHash", "CreatedAt")


@admin.register(PasswordHistory)
class PasswordHistoryAdmin(admin.ModelAdmin):
    list_display = ("UserID", "CreatedAt")
    search_fields = ("UserID__email",)
    readonly_fields = ("PasswordHash", "CreatedAt")


@admin.register(LoginAttempts)
class LoginAttemptsAdmin(admin.ModelAdmin):
    list_display = ("Email", "ApplicationCode", "Success", "IpAddress", "CreatedAt")
    list_filter = ("Success", "ApplicationCode")
    search_fields = ("Email", "IpAddress", "FailureReason")
    readonly_fields = ("CreatedAt",)


@admin.register(MfaMethods)
class MfaMethodsAdmin(admin.ModelAdmin):
    list_display = ("UserID", "MethodType", "IsEnabled", "VerifiedAt", "UpdatedAt")
    list_filter = ("MethodType", "IsEnabled")
    search_fields = ("UserID__email", "MethodType")
    readonly_fields = ("SecretHash", "CreatedAt", "UpdatedAt")


@admin.register(RecoveryCodes)
class RecoveryCodesAdmin(admin.ModelAdmin):
    list_display = ("UserID", "UsedAt", "CreatedAt")
    search_fields = ("UserID__email",)
    readonly_fields = ("CodeHash", "CreatedAt")


@admin.register(AccessAuditEvents)
class AccessAuditEventsAdmin(admin.ModelAdmin):
    list_display = ("EventType", "UserID", "ApplicationID", "IpAddress", "CreatedAt")
    list_filter = ("EventType", "ApplicationID")
    search_fields = ("UserID__email", "EventType", "IpAddress")
    readonly_fields = ("CreatedAt",)
