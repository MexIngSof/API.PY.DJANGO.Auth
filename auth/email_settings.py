from dataclasses import dataclass
from os import getenv

from django.core.exceptions import ImproperlyConfigured


EMAIL_PROJECT_CODES = (
    "AUTH",
    "REFAPART",
    "LEXNOVA",
    "JOBCRON",
    "DOCUCORE",
    "UNIVERSAL_POS",
    "MEXINGSOF",
    "TECNOTELEC",
    "CREACTIVA",
    "FISCORA",
)


@dataclass(frozen=True)
class ProjectEmailSettings:
    project_code: str
    provider: str
    access_key_id: str
    secret_access_key: str
    region_name: str
    smtp_host: str
    smtp_port: int | None
    smtp_use_tls: bool
    from_email: str
    configuration_set: str
    return_path: str
    support_email: str
    public_app_url: str
    source: str
    is_complete: bool


def resolve_email_backend(
    email_settings: ProjectEmailSettings,
    *,
    explicit_backend: str = "",
    deferred_external: bool = False,
) -> str:
    """Resolve Django's backend while preserving explicit project overrides."""
    if explicit_backend:
        return explicit_backend
    if email_settings.provider == "ses" and email_settings.is_complete:
        return "django_ses.SESBackend"
    if email_settings.provider == "mailpit":
        return "django.core.mail.backends.smtp.EmailBackend"
    if deferred_external:
        return "auth.email_backends.DeferredExternalEmailBackend"
    return "django.core.mail.backends.console.EmailBackend"


def _env(name: str) -> str:
    return getenv(name, "").strip()


def _project_value(project_code: str, key: str) -> tuple[str, str]:
    project_name = f"{project_code}_{key}"
    value = _env(project_name)
    if value:
        return value, project_name

    shared_name = f"AUTH_{key}"
    value = _env(shared_name)
    if value:
        return value, shared_name

    legacy_map = {
        "AWS_SES_ACCESS_KEY_ID": "AWS_SES_ACCESS_KEY_ID",
        "AWS_SES_SECRET_ACCESS_KEY": "AWS_SES_SECRET_ACCESS_KEY",
        "AWS_SES_REGION_NAME": "AWS_SES_REGION_NAME",
        "AWS_SES_FROM_EMAIL": "AWS_SES_FROM_EMAIL",
    }
    legacy_name = legacy_map.get(key)
    if legacy_name:
        value = _env(legacy_name)
        if value:
            return value, legacy_name

    return "", project_name


def get_email_settings(
    project_code: str = "AUTH",
    *,
    development_mode: bool = True,
    allow_deferred_external: bool = False,
) -> ProjectEmailSettings:
    """
    Resolve email settings for a project.

    Priority:
    1. Project-specific variables.
    2. Shared AUTH variables.
    3. Legacy AWS_SES variables for compatibility.
    4. Explicit AUTH_NOTIFICATION_FROM_EMAIL compatibility fallback.
    5. Empty sender in development when no sender is configured.
    """

    normalized_project_code = (project_code or "AUTH").strip().upper()
    provider, provider_source = _project_value(normalized_project_code, "EMAIL_PROVIDER")
    access_key_id, access_source = _project_value(normalized_project_code, "AWS_SES_ACCESS_KEY_ID")
    secret_access_key, secret_source = _project_value(
        normalized_project_code,
        "AWS_SES_SECRET_ACCESS_KEY",
    )
    region_name, region_source = _project_value(normalized_project_code, "AWS_SES_REGION_NAME")
    from_email, from_source = _project_value(normalized_project_code, "AWS_SES_FROM_EMAIL")
    configuration_set, config_source = _project_value(
        normalized_project_code,
        "AWS_SES_CONFIGURATION_SET",
    )
    return_path, return_path_source = _project_value(normalized_project_code, "EMAIL_RETURN_PATH")
    support_email, support_source = _project_value(normalized_project_code, "SUPPORT_EMAIL")
    public_app_url, url_source = _project_value(normalized_project_code, "PUBLIC_APP_URL")

    if not provider:
        provider = "ses" if any((access_key_id, secret_access_key, region_name, from_email)) else "console"
        provider_source = "derived"

    smtp_host = ""
    smtp_port: int | None = None
    smtp_use_tls = False
    smtp_sources: set[str] = set()
    is_mailpit = provider.lower() == "mailpit"
    if is_mailpit:
        smtp_host, smtp_host_source = _project_value(normalized_project_code, "EMAIL_SMTP_HOST")
        smtp_port_text, smtp_port_source = _project_value(normalized_project_code, "EMAIL_SMTP_PORT")
        smtp_tls_text, smtp_tls_source = _project_value(normalized_project_code, "EMAIL_SMTP_USE_TLS")
        smtp_host = smtp_host or "mailpit"
        try:
            smtp_port = int(smtp_port_text or "1025")
        except ValueError as error:
            raise ImproperlyConfigured("AUTH_EMAIL_SMTP_PORT must be an integer for Mailpit.") from error
        if not 1 <= smtp_port <= 65535:
            raise ImproperlyConfigured("AUTH_EMAIL_SMTP_PORT must be between 1 and 65535 for Mailpit.")
        smtp_use_tls = smtp_tls_text.lower() == "true"
        smtp_sources.update((smtp_host_source, smtp_port_source, smtp_tls_source))

    if not from_email:
        from_email = _env("AUTH_NOTIFICATION_FROM_EMAIL")
        from_source = "AUTH_NOTIFICATION_FROM_EMAIL" if from_email else "unconfigured"

    is_ses = provider.lower() == "ses"
    is_complete = bool(access_key_id and secret_access_key and region_name and from_email) if is_ses else True
    source = ",".join(
        sorted(
            {
                provider_source,
                access_source,
                secret_source,
                region_source,
                from_source,
                config_source,
                return_path_source,
                support_source,
                url_source,
                *smtp_sources,
            }
        )
    )

    if not development_mode and is_mailpit:
        raise ImproperlyConfigured("Mailpit email provider is allowed only in development/local certification.")

    if (
        not development_mode
        and not allow_deferred_external
        and (not provider or provider.lower() == "console" or not is_complete)
    ):
        missing = []
        if provider.lower() == "console":
            missing.append(f"{normalized_project_code}_EMAIL_PROVIDER")
        if is_ses:
            for name, value in (
                (f"{normalized_project_code}_AWS_SES_ACCESS_KEY_ID", access_key_id),
                (f"{normalized_project_code}_AWS_SES_SECRET_ACCESS_KEY", secret_access_key),
                (f"{normalized_project_code}_AWS_SES_REGION_NAME", region_name),
                (f"{normalized_project_code}_AWS_SES_FROM_EMAIL", from_email),
            ):
                if not value:
                    missing.append(name)
        raise ImproperlyConfigured(
            "Email provider is not completely configured for production. "
            f"Missing or invalid: {', '.join(missing) or normalized_project_code + '_EMAIL_PROVIDER'}"
        )

    return ProjectEmailSettings(
        project_code=normalized_project_code,
        provider=provider.lower(),
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        region_name=region_name,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_use_tls=smtp_use_tls,
        from_email=from_email,
        configuration_set=configuration_set,
        return_path=return_path,
        support_email=support_email,
        public_app_url=public_app_url,
        source=source,
        is_complete=is_complete,
    )
