from django.urls import path, re_path

from .mobile_session_views import CustomTokenRefreshView, LogoutView
from .views import (
    CustomProviderAuthView,
    CustomTokenObtainPairView,
    CustomTokenVerifyView,
    RequiredPasswordChangeView,
)

urlpatterns = [
    # ==========================
    # SOCIAL LOGIN
    # ==========================
    re_path(
        r'^o/(?P<provider>\S+)/$',
        CustomProviderAuthView.as_view(),
        name='provider-auth'
    ),

    # ==========================
    # JWT PERSONALIZADO
    # (NO pisa las rutas de DJOSER porque ahora están en api/jwt/)
    # ==========================
    path('jwt/create/', CustomTokenObtainPairView.as_view()),
    path('jwt/refresh/', CustomTokenRefreshView.as_view()),
    path('jwt/verify/', CustomTokenVerifyView.as_view()),
    path('password/change-required/', RequiredPasswordChangeView.as_view()),

    # ==========================
    # LOGOUT PERSONALIZADO
    # ==========================
    path('logout/', LogoutView.as_view()),
]
