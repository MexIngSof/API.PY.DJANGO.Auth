from django.conf import settings
from django.db import models

from roles.models import Roles


class Applications(models.Model):
    ApplicationID = models.AutoField(primary_key=True, db_column="Id")
    Code = models.CharField(max_length=50, unique=True, db_column="Code")
    Name = models.CharField(max_length=100, db_column="Name")
    Description = models.TextField(blank=True, null=True, db_column="Description")
    IsActive = models.BooleanField(default=True, db_column="IsActive")
    CreatedAt = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")
    UpdatedAt = models.DateTimeField(auto_now=True, db_column="UpdatedAt")

    class Meta:
        db_table = '"Auth"."Applications"'

    def __str__(self):
        return self.Code


class ApplicationEmailSettings(models.Model):
    ApplicationEmailSettingID = models.BigAutoField(primary_key=True, db_column="Id")
    ApplicationID = models.OneToOneField(
        Applications,
        on_delete=models.CASCADE,
        db_column="ApplicationId",
    )
    CommercialName = models.CharField(max_length=150, db_column="CommercialName")
    LogoUrl = models.URLField(max_length=500, blank=True, db_column="LogoUrl")
    PrimaryColor = models.CharField(max_length=20, blank=True, db_column="PrimaryColor")
    SenderEmail = models.EmailField(max_length=255, db_column="SenderEmail")
    SenderName = models.CharField(max_length=150, db_column="SenderName")
    BaseDomain = models.CharField(max_length=255, blank=True, db_column="BaseDomain")
    RedirectBaseUrl = models.URLField(max_length=500, blank=True, db_column="RedirectBaseUrl")
    IsActive = models.BooleanField(default=True, db_column="IsActive")
    CreatedAt = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")
    UpdatedAt = models.DateTimeField(auto_now=True, db_column="UpdatedAt")

    class Meta:
        db_table = '"Auth"."ApplicationEmailSettings"'

    def __str__(self):
        return f"{self.ApplicationID.Code} email settings"


class TransactionalEmailTemplates(models.Model):
    TransactionalEmailTemplateID = models.BigAutoField(primary_key=True, db_column="Id")
    ApplicationID = models.ForeignKey(
        Applications,
        on_delete=models.CASCADE,
        db_column="ApplicationId",
    )
    ActionCode = models.CharField(max_length=80, db_column="ActionCode")
    LanguageCode = models.CharField(max_length=10, default="es-MX", db_column="LanguageCode")
    Channel = models.CharField(max_length=30, default="EMAIL", db_column="Channel")
    SubjectTemplate = models.TextField(db_column="SubjectTemplate")
    TextBodyTemplate = models.TextField(blank=True, db_column="TextBodyTemplate")
    HtmlBodyTemplate = models.TextField(blank=True, db_column="HtmlBodyTemplate")
    IsActive = models.BooleanField(default=True, db_column="IsActive")
    CreatedAt = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")
    UpdatedAt = models.DateTimeField(auto_now=True, db_column="UpdatedAt")

    class Meta:
        db_table = '"Auth"."TransactionalEmailTemplates"'
        unique_together = ("ApplicationID", "ActionCode", "LanguageCode", "Channel")

    def __str__(self):
        return f"{self.ApplicationID.Code} {self.ActionCode} {self.LanguageCode}"


class EmailDeliveryLogs(models.Model):
    EmailDeliveryLogID = models.BigAutoField(primary_key=True, db_column="Id")
    ApplicationID = models.ForeignKey(
        Applications,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="ApplicationId",
    )
    TransactionalEmailTemplateID = models.ForeignKey(
        TransactionalEmailTemplates,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="TransactionalEmailTemplateId",
    )
    UserID = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="UserId",
    )
    ActionCode = models.CharField(max_length=80, db_column="ActionCode")
    ToEmail = models.EmailField(max_length=255, db_column="ToEmail")
    Subject = models.CharField(max_length=255, blank=True, db_column="Subject")
    Status = models.CharField(max_length=40, default="CREATED", db_column="Status")
    ErrorMessage = models.TextField(blank=True, db_column="ErrorMessage")
    CreatedAt = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")
    SentAt = models.DateTimeField(null=True, blank=True, db_column="SentAt")

    class Meta:
        db_table = '"Auth"."EmailDeliveryLogs"'

    def __str__(self):
        return f"{self.ActionCode} -> {self.ToEmail}"


class SocialProviders(models.Model):
    SocialProviderID = models.AutoField(primary_key=True, db_column="Id")
    Code = models.CharField(max_length=50, unique=True, db_column="Code")
    Name = models.CharField(max_length=100, db_column="Name")
    BackendName = models.CharField(max_length=100, unique=True, db_column="BackendName")
    IsActive = models.BooleanField(default=True, db_column="IsActive")
    CreatedAt = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")
    UpdatedAt = models.DateTimeField(auto_now=True, db_column="UpdatedAt")

    class Meta:
        db_table = '"Auth"."SocialProviders"'

    def __str__(self):
        return self.Code


class UserSocialAccounts(models.Model):
    UserSocialAccountID = models.BigAutoField(primary_key=True, db_column="Id")
    UserID = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="UserId",
    )
    SocialProviderID = models.ForeignKey(
        SocialProviders,
        on_delete=models.CASCADE,
        db_column="SocialProviderId",
    )
    ProviderUserId = models.CharField(max_length=255, db_column="ProviderUserId")
    Email = models.EmailField(max_length=255, blank=True, db_column="Email")
    DisplayName = models.CharField(max_length=255, blank=True, db_column="DisplayName")
    ProfileUrl = models.URLField(max_length=500, blank=True, db_column="ProfileUrl")
    AvatarUrl = models.URLField(max_length=500, blank=True, db_column="AvatarUrl")
    IsActive = models.BooleanField(default=True, db_column="IsActive")
    LastLoginAt = models.DateTimeField(null=True, blank=True, db_column="LastLoginAt")
    CreatedAt = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")
    UpdatedAt = models.DateTimeField(auto_now=True, db_column="UpdatedAt")

    class Meta:
        db_table = '"Auth"."UserSocialAccounts"'
        unique_together = ("SocialProviderID", "ProviderUserId")

    def __str__(self):
        return f"{self.UserID.email} - {self.SocialProviderID.Code}"


class SocialLoginAttempts(models.Model):
    SocialLoginAttemptID = models.BigAutoField(primary_key=True, db_column="Id")
    UserID = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="UserId",
    )
    SocialProviderID = models.ForeignKey(
        SocialProviders,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="SocialProviderId",
    )
    ApplicationCode = models.CharField(max_length=50, blank=True, db_column="ApplicationCode")
    Email = models.EmailField(max_length=255, blank=True, db_column="Email")
    IpAddress = models.GenericIPAddressField(null=True, blank=True, db_column="IpAddress")
    UserAgent = models.TextField(blank=True, db_column="UserAgent")
    Success = models.BooleanField(default=False, db_column="Success")
    FailureReason = models.CharField(max_length=255, blank=True, db_column="FailureReason")
    CreatedAt = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")

    class Meta:
        db_table = '"Auth"."SocialLoginAttempts"'

    def __str__(self):
        provider = self.SocialProviderID.Code if self.SocialProviderID else "UNKNOWN"
        status = "success" if self.Success else "failed"
        return f"{provider} {status}"


class Modules(models.Model):
    ModuleID = models.AutoField(primary_key=True, db_column="Id")
    Name = models.CharField(max_length=100, unique=True, db_column="Name")
    Description = models.TextField(blank=True, null=True, db_column="Description")
    Code = models.CharField(max_length=100, unique=True, db_column="Code")
    Path = models.CharField(max_length=255, db_column="Path")
    CreatedAt = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")
    UpdatedAt = models.DateTimeField(auto_now=True, db_column="UpdatedAt")

    class Meta:
        db_table = '"Auth"."Modules"'

    def __str__(self):
        return self.Name


class Actions(models.Model):
    ActionID = models.AutoField(primary_key=True, db_column="Id")
    Name = models.CharField(max_length=50, unique=True, db_column="Name")
    Description = models.TextField(blank=True, null=True, db_column="Description")
    CreatedAt = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")
    UpdatedAt = models.DateTimeField(auto_now=True, db_column="UpdatedAt")

    class Meta:
        db_table = '"Auth"."Actions"'

    def __str__(self):
        return self.Name


class Permissions(models.Model):
    PermissionID = models.AutoField(primary_key=True, db_column="Id")
    ModuleID = models.ForeignKey(Modules, on_delete=models.CASCADE, db_column="ModuleId")
    ActionID = models.ForeignKey(Actions, on_delete=models.CASCADE, db_column="ActionId")
    Code = models.CharField(max_length=150, unique=True, db_column="Code")
    CreatedAt = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")
    UpdatedAt = models.DateTimeField(auto_now=True, db_column="UpdatedAt")

    class Meta:
        db_table = '"Auth"."Permissions"'

    def __str__(self):
        return self.Code


class ApplicationRoles(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="Id")
    ApplicationID = models.ForeignKey(
        Applications,
        on_delete=models.CASCADE,
        db_column="ApplicationId",
    )
    RoleID = models.ForeignKey(Roles, on_delete=models.CASCADE, db_column="RoleId")
    CreatedAt = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")
    UpdatedAt = models.DateTimeField(auto_now=True, db_column="UpdatedAt")

    class Meta:
        db_table = '"Auth"."ApplicationRoles"'
        unique_together = ("ApplicationID", "RoleID")

    def __str__(self):
        return f"{self.ApplicationID.Code} -> {self.RoleID.Name}"


class ApplicationPermissions(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="Id")
    ApplicationID = models.ForeignKey(
        Applications,
        on_delete=models.CASCADE,
        db_column="ApplicationId",
    )
    PermissionID = models.ForeignKey(
        Permissions,
        on_delete=models.CASCADE,
        db_column="PermissionId",
    )
    CreatedAt = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")
    UpdatedAt = models.DateTimeField(auto_now=True, db_column="UpdatedAt")

    class Meta:
        db_table = '"Auth"."ApplicationPermissions"'
        unique_together = ("ApplicationID", "PermissionID")

    def __str__(self):
        return f"{self.ApplicationID.Code} -> {self.PermissionID.Code}"


class RolePermissions(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="Id")
    RoleID = models.ForeignKey(Roles, on_delete=models.CASCADE, db_column="RoleId")
    PermissionID = models.ForeignKey(
        Permissions,
        on_delete=models.CASCADE,
        db_column="PermissionId",
    )
    CreatedAt = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")
    UpdatedAt = models.DateTimeField(auto_now=True, db_column="UpdatedAt")

    class Meta:
        db_table = '"Auth"."RolePermissions"'
        unique_together = ("RoleID", "PermissionID")

    def __str__(self):
        return f"{self.RoleID.Name} -> {self.PermissionID.Code}"


class UserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="Id")
    UserID = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="UserId",
    )
    PermissionID = models.ForeignKey(
        Permissions,
        on_delete=models.CASCADE,
        db_column="PermissionId",
    )
    Allow = models.BooleanField(default=True, db_column="Allow")
    Reason = models.CharField(max_length=255, null=True, blank=True, db_column="Reason")
    CreatedAt = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")
    UpdatedAt = models.DateTimeField(auto_now=True, db_column="UpdatedAt")

    class Meta:
        db_table = '"Auth"."UserPermissions"'
        unique_together = ("UserID", "PermissionID")

    def __str__(self):
        status = "allow" if self.Allow else "deny"
        return f"{self.UserID.email} {status} {self.PermissionID.Code}"


class UserDevices(models.Model):
    DeviceID = models.BigAutoField(primary_key=True, db_column="Id")
    UserID = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="UserId",
    )
    DeviceName = models.CharField(max_length=150, blank=True, db_column="DeviceName")
    DeviceType = models.CharField(max_length=50, blank=True, db_column="DeviceType")
    OperatingSystem = models.CharField(max_length=100, blank=True, db_column="OperatingSystem")
    Browser = models.CharField(max_length=100, blank=True, db_column="Browser")
    IpAddress = models.GenericIPAddressField(null=True, blank=True, db_column="IpAddress")
    UserAgent = models.TextField(blank=True, db_column="UserAgent")
    FingerprintHash = models.CharField(max_length=128, db_column="FingerprintHash")
    IsTrusted = models.BooleanField(default=False, db_column="IsTrusted")
    IsActive = models.BooleanField(default=True, db_column="IsActive")
    LastSeenAt = models.DateTimeField(auto_now=True, db_column="LastSeenAt")
    CreatedAt = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")
    RevokedAt = models.DateTimeField(null=True, blank=True, db_column="RevokedAt")
    RevokedReason = models.CharField(max_length=255, blank=True, db_column="RevokedReason")

    class Meta:
        db_table = '"Auth"."UserDevices"'
        unique_together = ("UserID", "FingerprintHash")

    def __str__(self):
        return f"{self.UserID.email} - {self.DeviceName or self.DeviceType or 'device'}"


class UserSessions(models.Model):
    SessionID = models.BigAutoField(primary_key=True, db_column="Id")
    UserID = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="UserId",
    )
    DeviceID = models.ForeignKey(
        UserDevices,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="DeviceId",
    )
    ApplicationID = models.ForeignKey(
        Applications,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="ApplicationId",
    )
    AccessTokenJti = models.CharField(max_length=255, blank=True, db_column="AccessTokenJti")
    RefreshTokenHash = models.CharField(max_length=128, blank=True, db_column="RefreshTokenHash")
    StartedAt = models.DateTimeField(auto_now_add=True, db_column="StartedAt")
    LastActivityAt = models.DateTimeField(auto_now=True, db_column="LastActivityAt")
    ExpiresAt = models.DateTimeField(null=True, blank=True, db_column="ExpiresAt")
    RevokedAt = models.DateTimeField(null=True, blank=True, db_column="RevokedAt")
    RevokedReason = models.CharField(max_length=255, blank=True, db_column="RevokedReason")
    IsOnline = models.BooleanField(default=True, db_column="IsOnline")

    class Meta:
        db_table = '"Auth"."UserSessions"'

    def __str__(self):
        return f"{self.UserID.email} session {self.SessionID}"


class RefreshTokens(models.Model):
    RefreshTokenID = models.BigAutoField(primary_key=True, db_column="Id")
    UserID = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="UserId",
    )
    SessionID = models.ForeignKey(
        UserSessions,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="SessionId",
    )
    TokenHash = models.CharField(max_length=128, db_column="TokenHash")
    Jti = models.CharField(max_length=255, blank=True, db_column="Jti")
    ExpiresAt = models.DateTimeField(null=True, blank=True, db_column="ExpiresAt")
    RevokedAt = models.DateTimeField(null=True, blank=True, db_column="RevokedAt")
    RevokedReason = models.CharField(max_length=255, blank=True, db_column="RevokedReason")
    CreatedAt = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")

    class Meta:
        db_table = '"Auth"."RefreshTokens"'

    def __str__(self):
        return f"{self.UserID.email} refresh {self.RefreshTokenID}"


class PasswordHistory(models.Model):
    PasswordHistoryID = models.BigAutoField(primary_key=True, db_column="Id")
    UserID = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="UserId",
    )
    PasswordHash = models.CharField(max_length=255, db_column="PasswordHash")
    CreatedAt = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")

    class Meta:
        db_table = '"Auth"."PasswordHistory"'

    def __str__(self):
        return f"{self.UserID.email} password history {self.PasswordHistoryID}"


class LoginAttempts(models.Model):
    LoginAttemptID = models.BigAutoField(primary_key=True, db_column="Id")
    UserID = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="UserId",
    )
    Email = models.EmailField(max_length=255, blank=True, db_column="Email")
    ApplicationCode = models.CharField(max_length=50, blank=True, db_column="ApplicationCode")
    IpAddress = models.GenericIPAddressField(null=True, blank=True, db_column="IpAddress")
    UserAgent = models.TextField(blank=True, db_column="UserAgent")
    Success = models.BooleanField(default=False, db_column="Success")
    FailureReason = models.CharField(max_length=255, blank=True, db_column="FailureReason")
    CreatedAt = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")

    class Meta:
        db_table = '"Auth"."LoginAttempts"'

    def __str__(self):
        status = "success" if self.Success else "failed"
        return f"{self.Email or 'unknown'} {status}"


class MfaMethods(models.Model):
    MfaMethodID = models.BigAutoField(primary_key=True, db_column="Id")
    UserID = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="UserId",
    )
    MethodType = models.CharField(max_length=50, db_column="MethodType")
    SecretHash = models.CharField(max_length=255, blank=True, db_column="SecretHash")
    IsEnabled = models.BooleanField(default=False, db_column="IsEnabled")
    VerifiedAt = models.DateTimeField(null=True, blank=True, db_column="VerifiedAt")
    CreatedAt = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")
    UpdatedAt = models.DateTimeField(auto_now=True, db_column="UpdatedAt")

    class Meta:
        db_table = '"Auth"."MfaMethods"'

    def __str__(self):
        return f"{self.UserID.email} {self.MethodType}"


class RecoveryCodes(models.Model):
    RecoveryCodeID = models.BigAutoField(primary_key=True, db_column="Id")
    UserID = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="UserId",
    )
    CodeHash = models.CharField(max_length=255, db_column="CodeHash")
    UsedAt = models.DateTimeField(null=True, blank=True, db_column="UsedAt")
    CreatedAt = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")

    class Meta:
        db_table = '"Auth"."RecoveryCodes"'

    def __str__(self):
        return f"{self.UserID.email} recovery code {self.RecoveryCodeID}"


class AccessAuditEvents(models.Model):
    AccessAuditEventID = models.BigAutoField(primary_key=True, db_column="Id")
    UserID = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="UserId",
    )
    ApplicationID = models.ForeignKey(
        Applications,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="ApplicationId",
    )
    EventType = models.CharField(max_length=100, db_column="EventType")
    IpAddress = models.GenericIPAddressField(null=True, blank=True, db_column="IpAddress")
    UserAgent = models.TextField(blank=True, db_column="UserAgent")
    Metadata = models.JSONField(default=dict, blank=True, db_column="Metadata")
    CreatedAt = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")

    class Meta:
        db_table = '"Auth"."AccessAuditEvents"'

    def __str__(self):
        return f"{self.EventType} at {self.CreatedAt}"
