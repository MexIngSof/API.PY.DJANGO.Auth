from django.urls import path, include
from auth_health import health
from user.views import CustomUserViewSet

urlpatterns = [
    path('api/health/', health),

    # =====================================
    # DJOSER – RUTAS BASE DE USUARIOS
    # =====================================
    # /api/users/, /api/users/me/, etc.
    path(
        'api/users/reset_password/',
        CustomUserViewSet.as_view({'post': 'reset_password'}),
    ),
    path(
        'api/users/reset_password_confirm/',
        CustomUserViewSet.as_view({'post': 'reset_password_confirm'}),
    ),
    path('api/', include('djoser.urls')),
    # path('api/', include('djoser.urls.jwt')),    # /api/jwt/create/, /api/jwt/refresh/

    # =====================================
    # RUTAS PERSONALIZADAS POR PROYECTO
    # =====================================
    # <<-- Aquí van tus rutas custom SIN CHOCAR con Djoser
    path('api/auth/', include('user.urls')),
    path('api/access/', include('access.urls')),
    path('api/', include('access.urls')),
]

# Canonical container readiness endpoint. Keep unauthenticated and side-effect free.
from django.http import JsonResponse as _RuntimeJsonResponse

def _runtime_health(_request):
    return _RuntimeJsonResponse({"status": "ok"})

urlpatterns.insert(0, path("health/", _runtime_health))
