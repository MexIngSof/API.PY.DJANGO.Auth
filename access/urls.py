from django.urls import path
from .views import MePermissionsViewSet

me_permissions = MePermissionsViewSet.as_view({"get": "list_permissions"})

urlpatterns = [
    path("me/permissions/", me_permissions, name="me-permissions"),
]
