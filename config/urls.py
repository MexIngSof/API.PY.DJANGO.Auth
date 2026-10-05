from django.urls import include, path

from auth_health import health, ready
from user.scoped_views import ApplicationScopedUserViewSet

urlpatterns = [
    path("health/", health),
    path("ready/", ready),
    path("api/health/", health),
    path(
        "api/users/activation/",
        ApplicationScopedUserViewSet.as_view({"post": "activation"}),
    ),
    path(
        "api/users/resend_activation/",
        ApplicationScopedUserViewSet.as_view({"post": "resend_activation"}),
    ),
    path(
        "api/users/reset_password/",
        ApplicationScopedUserViewSet.as_view({"post": "reset_password"}),
    ),
    path(
        "api/users/reset_password_confirm/",
        ApplicationScopedUserViewSet.as_view({"post": "reset_password_confirm"}),
    ),
    path("api/", include("djoser.urls")),
    path("api/auth/", include("user.urls")),
    path("api/access/", include("access.urls")),
    path("api/", include("access.urls")),
]
