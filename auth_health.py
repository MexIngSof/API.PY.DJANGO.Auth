from django.http import JsonResponse


def health(_request):
    return JsonResponse({"service": "Auth", "status": "ok"})
