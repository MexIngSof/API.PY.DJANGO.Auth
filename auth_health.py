from django.db import connection
from django.http import JsonResponse


def health(_request):
    return JsonResponse({"service": "Auth", "status": "ok"})


def ready(_request):
    try:
        connection.ensure_connection()
    except Exception:
        return JsonResponse({"service": "Auth", "status": "not_ready"}, status=503)
    return JsonResponse({"service": "Auth", "status": "ready"})
