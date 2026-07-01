from django.urls import include, path
from rest_framework.routers import DefaultRouter

from access.views import (
    AccessAuditEventViewSet,
    ActionViewSet,
    ApplicationPermissionViewSet,
    ApplicationRoleViewSet,
    ApplicationViewSet,
    IdentityUserViewSet,
    LoginAttemptViewSet,
    MePermissionsViewSet,
    MfaMethodViewSet,
    ModuleViewSet,
    PasswordHistoryViewSet,
    PermissionViewSet,
    RecoveryCodeViewSet,
    RefreshTokenViewSet,
    RolePermissionViewSet,
    RoleViewSet,
    SocialLoginAttemptViewSet,
    SocialProviderViewSet,
    UserSocialAccountViewSet,
    UserDeviceViewSet,
    UserPermissionViewSet,
    UserSessionViewSet,
)


router = DefaultRouter()
router.register("applications", ApplicationViewSet, basename="applications")
router.register("identity/users", IdentityUserViewSet, basename="identity-users")
router.register("social-providers", SocialProviderViewSet, basename="social-providers")
router.register("social-accounts", UserSocialAccountViewSet, basename="social-accounts")
router.register("social-login-attempts", SocialLoginAttemptViewSet, basename="social-login-attempts")
router.register("modules", ModuleViewSet, basename="modules")
router.register("actions", ActionViewSet, basename="actions")
router.register("roles", RoleViewSet, basename="roles")
router.register("permissions", PermissionViewSet, basename="permissions")
router.register("role-permissions", RolePermissionViewSet, basename="role-permissions")
router.register("user-permissions", UserPermissionViewSet, basename="user-permissions")
router.register("application-roles", ApplicationRoleViewSet, basename="application-roles")
router.register(
    "application-permissions",
    ApplicationPermissionViewSet,
    basename="application-permissions",
)
router.register("devices", UserDeviceViewSet, basename="devices")
router.register("sessions", UserSessionViewSet, basename="sessions")
router.register("refresh-tokens", RefreshTokenViewSet, basename="refresh-tokens")
router.register("password-history", PasswordHistoryViewSet, basename="password-history")
router.register("login-attempts", LoginAttemptViewSet, basename="login-attempts")
router.register("mfa-methods", MfaMethodViewSet, basename="mfa-methods")
router.register("recovery-codes", RecoveryCodeViewSet, basename="recovery-codes")
router.register("audit-events", AccessAuditEventViewSet, basename="audit-events")

me_permissions = MePermissionsViewSet.as_view({"get": "list_permissions"})

urlpatterns = [
    path("", include(router.urls)),
    path("me/permissions/", me_permissions, name="me-permissions"),
]
