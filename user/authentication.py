from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.request import Request
from django.conf import settings

class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request: Request):
        # 1️⃣ Intentar Authorization header (Postman manual)
        header = self.get_header(request)
        if header is not None:
            raw_token = self.get_raw_token(header)
        else:
            # 2️⃣ Intentar cookie (Postman automático / frontend)
            raw_token = request.COOKIES.get(settings.AUTH_COOKIE)

        if raw_token is None:
            return None

        # ⚠️ AQUÍ NO HAY TRY/EXCEPT
        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)

        return user, validated_token
