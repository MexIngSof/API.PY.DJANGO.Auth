from rest_framework.exceptions import NotFound, PermissionDenied

from access.models import Applications
from user.application_scope import resolve_application_context


ADMIN_TARGET_QUERY_KEYS = ("application_code", "ApplicationCode")


def resolve_admin_target_application(request):
    """Resolve administrative target without allowing query params to define actor scope."""
    actor_application = resolve_application_context(
        request,
        trusted_target_query_keys=ADMIN_TARGET_QUERY_KEYS,
    )
    requested_code = ""
    for key in ADMIN_TARGET_QUERY_KEYS:
        value = request.query_params.get(key)
        if value not in (None, ""):
            requested_code = str(value).strip().upper()
            break

    if not requested_code or requested_code == actor_application.Code:
        return actor_application

    if not bool(getattr(request.user, "is_superuser", False)):
        raise PermissionDenied(
            "Delegated administrators may only administer their trusted application.",
            code="ADMIN_APPLICATION_SCOPE_DENIED",
        )

    target = Applications.objects.filter(Code=requested_code, IsActive=True).first()
    if target is None:
        raise NotFound(
            "Administrative target application is not registered or active.",
            code="ADMIN_APPLICATION_NOT_FOUND",
        )
    return target
