from django.contrib.auth import get_user_model


def normalize_email(email):
    return str(email or "").strip().lower()


def find_local_account(application, email, *, active_only=False):
    normalized_email = normalize_email(email)
    if application is None or not normalized_email:
        return None

    User = get_user_model()
    queryset = User.objects.filter(
        idApp=application.ApplicationID,
        email__iexact=normalized_email,
    )
    if active_only:
        queryset = queryset.filter(is_active=True)
    return queryset.first()


def account_belongs_to_application(user, application):
    if user is None or application is None:
        return False
    try:
        return int(user.idApp) == int(application.ApplicationID)
    except (TypeError, ValueError):
        return False
