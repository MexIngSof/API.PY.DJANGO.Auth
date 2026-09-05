from dataclasses import dataclass
from os import getenv
from urllib.parse import urlparse


@dataclass(frozen=True)
class CookiePolicy:
    secure: bool
    same_site: str
    domain: str | None


def _registrable_site(hostname: str) -> str:
    parts = [part for part in (hostname or "").lower().split(".") if part]
    if len(parts) <= 2:
        return ".".join(parts)
    return ".".join(parts[-2:])


def resolve_cookie_policy(
    *,
    environment: str | None = None,
    auth_origin: str | None = None,
    web_origins: list[str] | None = None,
    explicit_cross_site_origins: list[str] | None = None,
) -> CookiePolicy:
    """Return a safe cookie policy without requiring a hard-coded production hostname.

    Local HTTP remains host-only/Lax/non-Secure. HTTPS deployments are Secure. Lax is
    retained whenever all configured web origins share the same registrable site as Auth.
    True cross-site operation is allowed only for origins explicitly allow-listed by the
    operator, in which case SameSite=None is selected and the cookie remains host-only.
    """
    env = (environment or getenv("ENVIRONMENT") or "local").strip().lower()
    auth_origin = (auth_origin or getenv("AUTH_PUBLIC_ORIGIN") or "http://localhost:8000").strip()
    web_origins = web_origins if web_origins is not None else [
        item.strip() for item in getenv("AUTH_WEB_ORIGINS", "http://localhost:3000").split(",") if item.strip()
    ]
    explicit_cross_site_origins = explicit_cross_site_origins if explicit_cross_site_origins is not None else [
        item.strip() for item in getenv("AUTH_CROSS_SITE_ALLOWED_ORIGINS", "").split(",") if item.strip()
    ]

    parsed_auth = urlparse(auth_origin)
    auth_host = parsed_auth.hostname or "localhost"
    is_local_http = parsed_auth.scheme == "http" and auth_host in {"localhost", "127.0.0.1"}
    if env in {"local", "test", "development", "dev-local"} and is_local_http:
        return CookiePolicy(secure=False, same_site="Lax", domain=None)

    secure = parsed_auth.scheme == "https" or env in {"dev", "staging", "stage", "pro", "prod", "production"}
    auth_site = _registrable_site(auth_host)
    cross_site = []
    for origin in web_origins:
        parsed = urlparse(origin)
        if parsed.hostname and _registrable_site(parsed.hostname) != auth_site:
            cross_site.append(origin)

    if cross_site:
        allowed = set(explicit_cross_site_origins)
        not_allowed = [origin for origin in cross_site if origin not in allowed]
        if not_allowed:
            raise RuntimeError(
                "Cross-site Auth origins require explicit AUTH_CROSS_SITE_ALLOWED_ORIGINS: "
                + ",".join(not_allowed)
            )
        if not secure:
            raise RuntimeError("SameSite=None authentication cookies require HTTPS/Secure.")
        return CookiePolicy(secure=True, same_site="None", domain=None)

    return CookiePolicy(secure=secure, same_site="Lax", domain=None)
