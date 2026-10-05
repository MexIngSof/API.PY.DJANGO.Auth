import secrets

from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed

from access.models import Applications


APPLICATION_HEADER = "X-Application-Code"
GATEWAY_TOKEN_HEADER = "X-Gateway-Internal-Token"
CLIENT_APPLICATION_CODE_KEYS = ("ApplicationCode", "application_code")
CLIENT_APPLICATION_ID_KEYS = ("idApp", "ApplicationId", "application_id")


def _cache_application(request, application):
    setattr(request, "auth_application", application)
    setattr(request, "auth_application_code", application.Code)
    raw_request = getattr(request, "_request", None)
    if raw_request is not None:
        setattr(raw_request, "auth_application", application)
        setattr(raw_request, "auth_application_code", application.Code)


def _trusted_gateway_context(request):
    expected = str(getattr(settings, "GATEWAY_INTERNAL_SHARED_SECRET", "") or "")
    supplied = str(request.headers.get(GATEWAY_TOKEN_HEADER) or "")
    return bool(expected and supplied and secrets.compare_digest(expected, supplied))


def _request_value(request, key):
    data = getattr(request, "data", None)
    if hasattr(data, "get"):
        value = data.get(key)
        if value not in (None, ""):
            return value
    query_params = getattr(request, "query_params", None)
    if hasattr(query_params, "get"):
        value = query_params.get(key)
        if value not in (None, ""):
            return value
    return None


def _validate_client_context(request, application):
    for key in CLIENT_APPLICATION_CODE_KEYS:
        value = _request_value(request, key)
        if value is None:
            continue
        if str(value).strip().upper() != application.Code:
            raise AuthenticationFailed(
                "Client application context does not match the trusted Gateway context.",
                code="APPLICATION_CONTEXT_MISMATCH",
            )

    for key in CLIENT_APPLICATION_ID_KEYS:
        value = _request_value(request, key)
        if value is None:
            continue
        try:
            matches = int(value) == int(application.ApplicationID)
        except (TypeError, ValueError):
            matches = False
        if not matches:
            raise AuthenticationFailed(
                "Client application context does not match the trusted Gateway context.",
                code="APPLICATION_CONTEXT_MISMATCH",
            )


def resolve_application_context(request):
    cached = getattr(request, "auth_application", None)
    if cached is not None:
        return cached

    application_code = str(request.headers.get(APPLICATION_HEADER) or "").strip().upper()
    if not application_code:
        raise AuthenticationFailed(
            "X-Application-Code is required.",
            code="APPLICATION_CODE_REQUIRED",
        )

    if not _trusted_gateway_context(request):
        raise AuthenticationFailed(
            "A trusted Gateway context is required.",
            code="GATEWAY_CONTEXT_REQUIRED",
        )

    application = (
        Applications.objects.filter(Code=application_code, IsActive=True)
        .only("ApplicationID", "Code")
        .first()
    )
    if application is None:
        raise AuthenticationFailed(
            "Requested application is not registered or active.",
            code="APPLICATION_NOT_REGISTERED",
        )

    _validate_client_context(request, application)
    _cache_application(request, application)
    return application


def get_application_code(request):
    return resolve_application_context(request).Code
