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
    "IMAGRAFITY",
    "FISCORA",
)


@dataclass(frozen=True)
class ProjectEmailSettings:
    project_code: str
    provider: str
    access_key_id: str
    secret_access_key: str
    region_name: str
    from_email: str
    configuration_set: str
    return_path: str
    support_email: str
    public_app_url: str
    source: str
    is_complete: bool


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
    4. Safe console fallback only in development.
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

    if not from_email:
        from_email = _env("AUTH_NOTIFICATION_FROM_EMAIL") or "cash.1dip1@gmail.com"
        from_source = "AUTH_NOTIFICATION_FROM_EMAIL"

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
            }
        )
    )

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
        from_email=from_email,
        configuration_set=configuration_set,
        return_path=return_path,
        support_email=support_email,
        public_app_url=public_app_url,
        source=source,
        is_complete=is_complete,
    )
