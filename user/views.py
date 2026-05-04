from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request
from djoser.social.views import ProviderAuthView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

# Esta clase extiende el login con proveedor externo (OAuth) de Djoser
class CustomProviderAuthView(ProviderAuthView):
    def post(self, request, *args, **kwargs):
        # Llama al método original para autenticar y obtener la respuesta
        response = super().post(request, *args, **kwargs)

        # Si la autenticación fue exitosa (201 Created)
        if response.status_code == 201:
            # Extrae los tokens del cuerpo de la respuesta
            access_token = response.data.get('access')
            refresh_token = response.data.get('refresh')
            
            # Guarda el token de acceso como cookie segura
            response.set_cookie(
                'access',
                access_token,
                max_age=settings.AUTH_COOKIE_ACCESS_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE
            )

            # Guarda el token de actualización también como cookie segura
            response.set_cookie(
                'refresh',
                refresh_token,
                max_age=settings.AUTH_COOKIE_ACCESS_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE
            )

        return response

# Esta clase sobreescribe la vista de obtención de tokens con JWT (login con usuario/contraseña)
class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request: Request, *args, **kwargs) -> Response:
        # Llama al método original para procesar el login
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            access_token  = response.data.get('access')
            refresh_token = response.data.get('refresh')

            # Almacena ambos tokens en cookies seguras
            response.set_cookie(
                'access',
                access_token,
                max_age=settings.AUTH_COOKIE_ACCESS_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE
            )

            response.set_cookie(
                'refresh',
                refresh_token,
                max_age=settings.AUTH_COOKIE_REFRESH_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE
            )

        return response

# Esta clase sobreescribe la vista de refresco del token de acceso usando el refresh token
class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request: Request, *args, **kwargs) -> Response:
        # Toma el refresh token directamente desde las cookies
        refresh_token = request.COOKIES.get('refresh')

        if refresh_token:
            request.data['refresh'] = refresh_token

        # Ejecuta el refresco normalmente
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            access_token = response.data.get('access')

            # Actualiza la cookie con el nuevo token de acceso
            response.set_cookie(
                'access',
                access_token,
                max_age=settings.AUTH_COOKIE_ACCESS_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE
            )

        return response

# Esta clase sobreescribe la verificación del token accediendo al token desde cookies
class CustomTokenVerifyView(TokenVerifyView):
    def post(self, request: Request, *args, **kwargs) -> Response:
        # Toma el token de acceso desde la cookie
        access_token = request.COOKIES.get('access')

        if access_token:
            request.data['token'] = access_token

        # Llama a la vista original con el token actualizado
        return super().post(request, *args, **kwargs)

# Esta vista elimina las cookies y "cierra sesión" efectivamente
class LogoutView(APIView):
    def post(self, request, *args, **kwargs):
        # Crea una respuesta vacía con código 204 (sin contenido)
        response = Response(status=status.HTTP_204_NO_CONTENT)

        # Elimina ambas cookies
        response.delete_cookie('access')
        response.delete_cookie('refresh')

        return response
