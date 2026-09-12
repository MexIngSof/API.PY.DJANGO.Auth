from django.urls import include, path

from auth_health import health, ready
from user.views import CustomUserViewSet

urlpatterns = [
    path("health/", health),
    path("ready/", ready),
    path("api/health/", health),
    path(
        "api/users/reset_password/",
        CustomUserViewSet.as_view({"post": "reset_password"}),
    ),
    path(
        "api/users/reset_password_confirm/",
        CustomUserViewSet.as_view({"post": "reset_password_confirm"}),
    ),
    path("api/", include("djoser.urls")),
    path("api/auth/", include("user.urls")),
    path("api/access/", include("access.urls")),
    path("api/", include("access.urls")),
]
