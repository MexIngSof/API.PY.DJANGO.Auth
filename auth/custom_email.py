from django.template import Context, Template, TemplateDoesNotExist
from django.template.loader import get_template
from django.utils import timezone
from djoser import email


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
        self.template_name = self.resolve_template_name(application)
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

        if application is None:
            application = Applications.objects.filter(Code="TECNOTELEC", IsActive=True).first()

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

    def resolve_template_name(self, application):
        action_template_name = ACTION_TEMPLATE_NAMES.get(self.action_code)
        if application is None or not action_template_name:
            return self.template_name

        custom_template_name = (
            f"auth_emails/{application.Code.lower()}/{action_template_name}.html"
        )
        try:
            get_template(custom_template_name)
        except TemplateDoesNotExist:
            return self.template_name
        return custom_template_name

    def render(self):
        context = self.get_context_data()
        template = getattr(self, "auth_email_template", None)

        if template is None:
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
        user = self.context.get("user") if hasattr(self, "context") else None
        to_email = to[0] if isinstance(to, (list, tuple)) and to else str(to)

        if email_settings is not None:
            kwargs.setdefault(
                "from_email",
                f"{email_settings.SenderName} <{email_settings.SenderEmail}>",
            )

        try:
            response = super().send(to, *args, **kwargs)
            EmailDeliveryLogs.objects.create(
                ApplicationID=application,
                TransactionalEmailTemplateID=template,
                UserID=user if getattr(user, "pk", None) else None,
                ActionCode=self.action_code,
                ToEmail=to_email,
                Subject=getattr(self, "subject", ""),
                Status="SENT",
                SentAt=timezone.now(),
            )
            return response
        except Exception as exc:
            EmailDeliveryLogs.objects.create(
                ApplicationID=application,
                TransactionalEmailTemplateID=template,
                UserID=user if getattr(user, "pk", None) else None,
                ActionCode=self.action_code,
                ToEmail=to_email,
                Subject=getattr(self, "subject", ""),
                Status="FAILED",
                ErrorMessage=str(exc),
            )
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
