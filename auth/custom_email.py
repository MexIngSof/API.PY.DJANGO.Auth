import hashlib
import logging
import re
from email.mime.image import MIMEImage
from pathlib import Path

from django.conf import settings
from django.template import Context, Template, TemplateDoesNotExist
from django.template.loader import get_template
from django.utils import timezone
from djoser import email

from auth.email_settings import get_email_settings

logger = logging.getLogger(__name__)


ACTION_ACTIVATION = "VERIFY_ACCOUNT"
ACTION_CONFIRMATION = "REGISTER"
ACTION_PASSWORD_RESET = "PASSWORD_RESET"
ACTION_PASSWORD_CHANGED = "PASSWORD_CHANGED"
ACTION_EMAIL_RESET = "EMAIL_RESET"
ACTION_EMAIL_CHANGED = "EMAIL_CHANGED"

ACTION_LABELS = {
    ACTION_ACTIVATION: "Confirmacion de cuenta",
    ACTION_CONFIRMATION: "Registro de usuario",
    ACTION_PASSWORD_RESET: "Recuperacion de password",
    ACTION_PASSWORD_CHANGED: "Password cambiado",
    ACTION_EMAIL_RESET: "Cambio de email solicitado",
    ACTION_EMAIL_CHANGED: "Email cambiado",
}

ACTION_TEMPLATE_NAMES = {
    ACTION_ACTIVATION: "verify_account",
    ACTION_CONFIRMATION: "register",
    ACTION_PASSWORD_RESET: "password_reset",
    ACTION_PASSWORD_CHANGED: "password_changed",
    ACTION_EMAIL_RESET: "email_reset",
    ACTION_EMAIL_CHANGED: "email_changed",
}

TEMPLATE_SOURCE_FILE = "FILE"
TEMPLATE_SOURCE_DB_FALLBACK = "DB_FALLBACK"
TEMPLATE_SOURCE_DJOSER_FALLBACK = "DJOSER_FALLBACK"

REFAPART_TEMPLATE_PREFIX = "auth_emails/refapart/"
REFAPART_LOGO_CONTENT_ID = "refapart-logo"
REFAPART_LOGO_FILENAME = "refapart-logo-with-tagline.png"
REFAPART_LOGO_PATH = Path("templates/auth_emails/refapart/assets") / REFAPART_LOGO_FILENAME


def mask_email(email_address):
    if not email_address or "@" not in email_address:
        return ""
    local, domain = email_address.split("@", 1)
    if len(local) <= 2:
        local_mask = f"{local[:1]}***"
    else:
        local_mask = f"{local[:2]}***{local[-1:]}"
    return f"{local_mask}@{domain}"


def hash_email(email_address):
    if not email_address:
        return ""
    return f"sha256:{hashlib.sha256(email_address.lower().encode()).hexdigest()}"


def provider_name(email_config=None):
    if email_config is not None:
        return email_config.provider.upper()
    backend = getattr(settings, "EMAIL_BACKEND", "")
    if "ses" in backend.lower():
        return "SES"
    if "smtp" in backend.lower():
        return "SMTP"
    if "console" in backend.lower():
        return "CONSOLE"
    return backend.rsplit(".", 1)[-1].upper() if backend else "UNKNOWN"


def classify_email_error(exc):
    message = str(exc)
    normalized = message.lower()
    if "accessdenied" in normalized or "not authorized" in normalized or "not authorised" in normalized:
        return "SES_ACCESS_DENIED"
    if "region" in normalized:
        return "SES_REGION_MISSING"
    if "credential" in normalized or "signature" in normalized or "access key" in normalized:
        return "SES_CREDENTIALS_INVALID"
    if "sandbox" in normalized:
        return "SES_SANDBOX_ENABLED"
    if "domain" in normalized and "verif" in normalized:
        return "SES_DOMAIN_NOT_VERIFIED"
    if "quota" in normalized:
        return "SES_QUOTA_EXCEEDED"
    if "throttl" in normalized or "rate" in normalized:
        return "SES_THROTTLED"
    if "timeout" in normalized:
        return "EMAIL_PROVIDER_TIMEOUT"
    return "EMAIL_PROVIDER_UNAVAILABLE"


def get_application_code(request):
    if request is None:
        return ""
    return (
        request.POST.get("ApplicationCode")
        or request.POST.get("application_code")
        or request.GET.get("application_code")
        or request.headers.get("X-Application-Code")
        or ""
    ).strip().upper()


class AuthTransactionalEmailMixin:
    action_code = ""

    def get_context_data(self):
        context = super().get_context_data()
        application, email_settings, template = self.resolve_email_metadata(context)

        commercial_name = (
            email_settings.CommercialName
            if email_settings is not None
            else context.get("site_name", "")
        )
        raw_url = str(context.get("url", "")).lstrip("/")
        if email_settings is not None and email_settings.RedirectBaseUrl:
            action_url = f"{email_settings.RedirectBaseUrl.rstrip('/')}/{raw_url}".rstrip("/")
        else:
            action_url = f"{context.get('protocol')}://{context.get('domain')}/{raw_url}".rstrip("/")

        context.update(
            {
                "application": application,
                "application_code": application.Code if application else "",
                "commercial_name": commercial_name,
                "logo_url": email_settings.LogoUrl if email_settings else "",
                "primary_color": email_settings.PrimaryColor if email_settings else "",
                "sender_name": email_settings.SenderName if email_settings else "",
                "redirect_base_url": email_settings.RedirectBaseUrl if email_settings else "",
                "action_code": self.action_code,
                "action_name": ACTION_LABELS.get(self.action_code, self.action_code),
                "action_url": action_url,
            }
        )
        self.auth_email_application = application
        self.auth_email_settings = email_settings
        self.auth_email_template = template
        self.auth_email_file_template_name = self.resolve_file_template_name(application)
        self.auth_email_template_source = self.resolve_template_source(
            self.auth_email_file_template_name,
            template,
        )
        if self.auth_email_file_template_name:
            self.template_name = self.auth_email_file_template_name
        return context

    def resolve_email_metadata(self, context):
        from access.models import (
            ApplicationEmailSettings,
            Applications,
            TransactionalEmailTemplates,
        )

        application_code = get_application_code(self.request)
        application = None

        if application_code:
            application = Applications.objects.filter(Code=application_code, IsActive=True).first()

        user = context.get("user")
        if application is None and getattr(user, "idApp", None):
            application = Applications.objects.filter(
                ApplicationID=user.idApp,
                IsActive=True,
            ).first()

        if application is None:
            logger.warning(
                "auth.email.application.unresolved",
                extra={
                    "event": "auth.email.application.unresolved",
                    "action_code": self.action_code,
                    "requested_application_code": application_code,
                    "has_user_application": bool(getattr(user, "idApp", None)),
                },
            )

        email_settings = None
        template = None

        if application is not None:
            email_settings = ApplicationEmailSettings.objects.filter(
                ApplicationID=application,
                IsActive=True,
            ).first()
            template = TransactionalEmailTemplates.objects.filter(
                ApplicationID=application,
                ActionCode=self.action_code,
                LanguageCode=context.get("language_code", "es-MX"),
                Channel="EMAIL",
                IsActive=True,
            ).first()

        return application, email_settings, template

    def resolve_file_template_name(self, application):
        action_template_name = ACTION_TEMPLATE_NAMES.get(self.action_code)
        if application is None or not action_template_name:
            return ""

        custom_template_name = (
            f"auth_emails/{application.Code.lower()}/{action_template_name}.html"
        )
        try:
            get_template(custom_template_name)
        except TemplateDoesNotExist:
            return ""
        return custom_template_name

    def resolve_template_source(self, file_template_name, db_template):
        if file_template_name:
            return TEMPLATE_SOURCE_FILE
        if db_template is not None:
            return TEMPLATE_SOURCE_DB_FALLBACK
        return TEMPLATE_SOURCE_DJOSER_FALLBACK

    def render_block_from_file_template(self, file_template_name, block_name, context):
        template = get_template(file_template_name)
        origin_name = getattr(getattr(template, "origin", None), "name", "")
        if not origin_name:
            return ""

        with open(origin_name, encoding="utf-8") as template_file:
            source = template_file.read()

        pattern = (
            r"{%\s*block\s+"
            + re.escape(block_name)
            + r"\s*%}(.*?){%\s*endblock(?:\s+"
            + re.escape(block_name)
            + r")?\s*%}"
        )
        match = re.search(pattern, source, flags=re.DOTALL)
        if not match:
            return ""

        return Template(match.group(1)).render(Context(context)).strip()

    def render_html_from_file_template(self, file_template_name, context):
        rendered = get_template(file_template_name).render(context)
        doctype_index = rendered.lower().find("<!doctype html>")
        if doctype_index >= 0:
            return rendered[doctype_index:].strip()
        return rendered.strip()

    def attach_file_template_inline_assets(self, file_template_name):
        if not file_template_name.startswith(REFAPART_TEMPLATE_PREFIX):
            return

        if not hasattr(self, "attachments"):
            self.attachments = []

        content_id = f"<{REFAPART_LOGO_CONTENT_ID}>"
        for attachment in getattr(self, "attachments", []):
            if hasattr(attachment, "get") and attachment.get("Content-ID") == content_id:
                return

        logo_path = Path(settings.BASE_DIR) / REFAPART_LOGO_PATH
        if not logo_path.exists():
            logger.warning(
                "auth.email.inline_asset.missing",
                extra={
                    "event": "auth.email.inline_asset.missing",
                    "template_path": file_template_name,
                    "asset_path": str(logo_path),
                    "content_id": REFAPART_LOGO_CONTENT_ID,
                },
            )
            return

        logo = MIMEImage(logo_path.read_bytes(), _subtype="png")
        logo.add_header("Content-ID", content_id)
        logo.add_header("Content-Disposition", "inline", filename=REFAPART_LOGO_FILENAME)
        self.attach(logo)

    def render(self):
        context = self.get_context_data()
        template = getattr(self, "auth_email_template", None)
        template_source = getattr(
            self,
            "auth_email_template_source",
            TEMPLATE_SOURCE_DJOSER_FALLBACK,
        )
        file_template_name = getattr(self, "auth_email_file_template_name", "")

        if template_source == TEMPLATE_SOURCE_FILE:
            self.subject = self.render_block_from_file_template(
                file_template_name,
                "subject",
                context,
            )
            self.auth_email_text_body = self.render_block_from_file_template(
                file_template_name,
                "text_body",
                context,
            )
            self.body = ""
            self.html = self.render_html_from_file_template(file_template_name, context)
            self._attach_body()
            self.attach_file_template_inline_assets(file_template_name)
            return

        if template_source != TEMPLATE_SOURCE_DB_FALLBACK:
            return super().render()

        render_context = Context(context)
        self.subject = Template(template.SubjectTemplate).render(render_context).strip()
        self.body = Template(template.TextBodyTemplate).render(render_context).strip()
        self.html = Template(template.HtmlBodyTemplate).render(render_context).strip()
        self._attach_body()

    def send(self, to, *args, **kwargs):
        from access.models import EmailDeliveryLogs

        application = getattr(self, "auth_email_application", None)
        email_settings = getattr(self, "auth_email_settings", None)
        template = getattr(self, "auth_email_template", None)
        file_template_name = getattr(self, "auth_email_file_template_name", "")
        template_source = getattr(
            self,
            "auth_email_template_source",
            TEMPLATE_SOURCE_DJOSER_FALLBACK,
        )
        user = self.context.get("user") if hasattr(self, "context") else None
        to_email = to[0] if isinstance(to, (list, tuple)) and to else str(to)
        request = getattr(self, "request", None)
        request_id = request.headers.get("X-Request-ID", "") if request else ""
        correlation_id = request.headers.get("X-Correlation-ID", "") if request else ""
        application_code = application.Code if application else get_application_code(request) or "AUTH"
        resolved_email_settings = get_email_settings(
            application_code,
            development_mode=getattr(settings, "DEVELOPMENT_MODE", True),
        )
        provider = provider_name(resolved_email_settings)

        if email_settings is not None:
            kwargs.setdefault(
                "from_email",
                f"{email_settings.SenderName} <{email_settings.SenderEmail}>",
            )
        elif resolved_email_settings.from_email:
            kwargs.setdefault("from_email", resolved_email_settings.from_email)

        delivery_log = EmailDeliveryLogs.objects.create(
            ApplicationID=application,
            TransactionalEmailTemplateID=template,
            UserID=user if getattr(user, "pk", None) else None,
            ActionCode=self.action_code,
            ToEmail=to_email,
            Subject=getattr(self, "subject", ""),
            Status="PROCESSING",
            Provider=provider,
            CorrelationId=correlation_id,
            RequestId=request_id,
            ProviderResponsePayload={
                "config_source": resolved_email_settings.source,
                "project_code": resolved_email_settings.project_code,
                "provider_complete": resolved_email_settings.is_complete,
                "template_source": template_source,
                "resolved_template_path": file_template_name,
                "application_code": application_code,
                "action_code": self.action_code,
                "has_db_template": template is not None,
                "has_file_template": bool(file_template_name),
            },
        )

        try:
            response = super().send(to, *args, **kwargs)
            extra_headers = getattr(self, "extra_headers", {})
            ses_status = str(extra_headers.get("status") or "")
            ses_message_id = extra_headers.get("message_id")
            ses_request_id = extra_headers.get("request_id")
            provider_accepted = bool(response) or ses_status == "200" or bool(ses_message_id or ses_request_id)
            delivery_log.Status = "SENT" if provider_accepted else "FAILED"
            delivery_log.ProviderResponseCode = str(response)
            delivery_log.ProviderResponsePayload = {
                "backend": getattr(settings, "EMAIL_BACKEND", ""),
                "result": response,
                "config_source": resolved_email_settings.source,
                "project_code": resolved_email_settings.project_code,
                "provider_complete": resolved_email_settings.is_complete,
                "template_source": template_source,
                "resolved_template_path": file_template_name,
                "application_code": application_code,
                "action_code": self.action_code,
                "has_db_template": template is not None,
                "has_file_template": bool(file_template_name),
                "ses_status": extra_headers.get("status"),
                "ses_message_id": ses_message_id,
                "ses_request_id": ses_request_id,
            }
            delivery_log.ProviderMessageId = ses_message_id or ""
            delivery_log.ProviderRequestId = ses_request_id or ""
            delivery_log.SentAt = timezone.now() if provider_accepted else None
            if not provider_accepted:
                delivery_log.LastErrorCode = "EMAIL_PROVIDER_UNAVAILABLE"
                delivery_log.FailureReason = (
                    extra_headers.get("error_message")
                    or extra_headers.get("reason")
                    or "Email backend returned no accepted recipients."
                )
                delivery_log.ErrorMessage = delivery_log.FailureReason
                delivery_log.ProviderResponsePayload = {
                    **delivery_log.ProviderResponsePayload,
                    "ses_status": extra_headers.get("status"),
                    "ses_reason": extra_headers.get("reason"),
                    "ses_error_code": extra_headers.get("error_code"),
                    "ses_error_message": extra_headers.get("error_message"),
                    "ses_request_id": extra_headers.get("request_id"),
                }
            delivery_log.save(
                update_fields=[
                    "Status",
                    "ProviderResponseCode",
                    "ProviderResponsePayload",
                    "SentAt",
                    "ProviderMessageId",
                    "ProviderRequestId",
                    "LastErrorCode",
                    "FailureReason",
                    "ErrorMessage",
                ]
            )
            logger.info(
                "auth.email.delivery.%s",
                "sent" if provider_accepted else "failed",
                extra={
                    "event": (
                        "auth.email.delivery.sent"
                        if provider_accepted
                        else "auth.email.delivery.failed"
                    ),
                    "application_code": application_code,
                    "action_code": self.action_code,
                    "email_hash": hash_email(to_email),
                    "email_mask": mask_email(to_email),
                    "provider": provider,
                    "provider_response_code": str(response),
                    "correlation_id": correlation_id,
                    "request_id": request_id,
                    "retry_count": delivery_log.RetryCount,
                    "error_code": delivery_log.LastErrorCode,
                },
            )
            return response
        except Exception as exc:
            error_code = classify_email_error(exc)
            delivery_log.Status = "FAILED"
            delivery_log.ErrorMessage = str(exc)
            delivery_log.FailureReason = str(exc)
            delivery_log.LastErrorCode = error_code
            delivery_log.ProviderResponsePayload = {
                "backend": getattr(settings, "EMAIL_BACKEND", ""),
                "exception_type": exc.__class__.__name__,
                "config_source": resolved_email_settings.source,
                "project_code": resolved_email_settings.project_code,
                "provider_complete": resolved_email_settings.is_complete,
                "template_source": template_source,
                "resolved_template_path": file_template_name,
                "application_code": application_code,
                "action_code": self.action_code,
                "has_db_template": template is not None,
                "has_file_template": bool(file_template_name),
            }
            delivery_log.save(
                update_fields=[
                    "Status",
                    "ErrorMessage",
                    "FailureReason",
                    "LastErrorCode",
                    "ProviderResponsePayload",
                ]
            )
            logger.exception(
                "auth.email.delivery.failed",
                extra={
                    "event": "auth.email.delivery.failed",
                    "application_code": application_code,
                    "action_code": self.action_code,
                    "email_hash": hash_email(to_email),
                    "email_mask": mask_email(to_email),
                    "provider": provider,
                    "correlation_id": correlation_id,
                    "request_id": request_id,
                    "retry_count": delivery_log.RetryCount,
                    "error_code": error_code,
                },
            )
            if getattr(settings, "AUTH_EMAIL_DELIVERY_FAIL_OPEN", True):
                return 0
            raise


class ActivationEmail(AuthTransactionalEmailMixin, email.ActivationEmail):
    action_code = ACTION_ACTIVATION
    template_name = "djoser/email/activation.html"


class ConfirmationEmail(AuthTransactionalEmailMixin, email.ConfirmationEmail):
    action_code = ACTION_CONFIRMATION
    template_name = "djoser/email/activation.html"


class PasswordResetEmail(AuthTransactionalEmailMixin, email.PasswordResetEmail):
    action_code = ACTION_PASSWORD_RESET
    template_name = "djoser/email/password_reset.html"


class PasswordChangedConfirmationEmail(
    AuthTransactionalEmailMixin,
    email.PasswordChangedConfirmationEmail,
):
    action_code = ACTION_PASSWORD_CHANGED
    template_name = "djoser/email/password_reset.html"


class UsernameResetEmail(AuthTransactionalEmailMixin, email.UsernameResetEmail):
    action_code = ACTION_EMAIL_RESET
    template_name = "djoser/email/password_reset.html"


class UsernameChangedConfirmationEmail(
    AuthTransactionalEmailMixin,
    email.UsernameChangedConfirmationEmail,
):
    action_code = ACTION_EMAIL_CHANGED
    template_name = "djoser/email/password_reset.html"
