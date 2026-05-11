from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Panel admin
    path('admin/', admin.site.urls),

    # =====================================
    # DJOSER – RUTAS BASE DE USUARIOS
    # =====================================
    # /api/users/, /api/users/me/, etc.
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
