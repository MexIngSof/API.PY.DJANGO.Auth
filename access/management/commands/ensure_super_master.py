import os
from urllib.parse import urlparse

from django.conf import settings as django_settings
from django.core.management.base import BaseCommand, CommandError
from django.test import RequestFactory
from djoser.conf import settings as djoser_settings

from access.models import Applications, EmailDeliveryLogs
from auth.email_settings import get_email_settings
from roles.models import Roles, UserRoles
from user.models import UserAccount


APPLICATION_CODE = "JOBCRON"
ROLE_NAME = "JOBCRON_SUPER_ADMIN"
PASSWORD_RESET_ACTION = "PASSWORD_RESET"
ACCEPTED_DELIVERY_STATUSES = {
    "SENT",
    "ACCEPTED_BY_PROVIDER",
    "DELIVERED",
    "OPENED",
}


def is_enabled(value):
    return str(value).lower() in {"true", "1", "yes"}


def has_accepted_setup_email(user):
    return EmailDeliveryLogs.objects.filter(
        UserID=user,
        ActionCode=PASSWORD_RESET_ACTION,
        Status__in=ACCEPTED_DELIVERY_STATUSES,
    ).exists()


def send_setup_email(user):
    public_url = get_email_settings(
        APPLICATION_CODE,
        development_mode=django_settings.DEVELOPMENT_MODE,
    ).public_app_url or "http://localhost:3000"
    parsed_url = urlparse(public_url)
    request = RequestFactory().post(
        "/api/users/reset_password/",
        data={"email": user.email},
        content_type="application/json",
        secure=parsed_url.scheme == "https",
        HTTP_X_APPLICATION_CODE=APPLICATION_CODE,
        HTTP_HOST=parsed_url.netloc or "localhost:3000",
    )
    djoser_settings.EMAIL.password_reset(request, {"user": user}).send([user.email])


class Command(BaseCommand):
    help = "Ensures the JobCron Super Master user exists without overwriting its password."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            default=os.getenv("JOBCRON_SUPERMASTER_EMAIL", ""),
            help="Super Master email. Defaults to JOBCRON_SUPERMASTER_EMAIL.",
        )
        parser.add_argument(
            "--enabled",
            default=os.getenv("JOBCRON_SUPERMASTER_BOOTSTRAP_ENABLED", "false"),
            choices=("true", "false", "1", "0", "yes", "no"),
            help="Bootstrap guard. Defaults to JOBCRON_SUPERMASTER_BOOTSTRAP_ENABLED.",
        )
        parser.add_argument(
            "--send-setup-email",
            default=os.getenv("JOBCRON_SUPERMASTER_SEND_SETUP_EMAIL", "true"),
            choices=("true", "false", "1", "0", "yes", "no"),
            help="Send the first-access password setup email when needed.",
        )
        parser.add_argument(
            "--resend-setup-email",
            action="store_true",
            help="Resend even when a previous setup email was accepted.",
        )

    def handle(self, *args, **options):
        enabled = is_enabled(options["enabled"])
        if not enabled:
            self.stdout.write(
                "Super Master bootstrap skipped. Set JOBCRON_SUPERMASTER_BOOTSTRAP_ENABLED=true to enable it."
            )
            return

        email = (options["email"] or "").strip().lower()
        if not email:
            raise CommandError("JOBCRON_SUPERMASTER_EMAIL is required.")

        application, _ = Applications.objects.update_or_create(
            Code=APPLICATION_CODE,
            defaults={
                "Name": "JobCron",
                "Description": "Centro administrativo global del ecosistema.",
                "IsActive": True,
            },
        )
        role, _ = Roles.objects.update_or_create(
            Name=ROLE_NAME,
            defaults={
                "DisplayName": "Super Master JobCron",
                "Description": "Control total de JobCron y gobierno global del ecosistema.",
            },
        )

        user = UserAccount.objects.filter(email=email).first()
        created = user is None
        password_was_usable = False

        if created:
            user = UserAccount(
                email=email,
                first_name="Super",
                last_name="Master JobCron",
                is_active=True,
                is_staff=True,
                is_superuser=True,
                must_change_password=True,
                idApp=application.ApplicationID,
            )
            user.set_unusable_password()
            user.save()
        else:
            password_was_usable = user.has_usable_password()
            update_fields = []
            for field, value in (
                ("first_name", user.first_name or "Super"),
                ("last_name", user.last_name or "Master JobCron"),
                ("is_active", True),
                ("is_staff", True),
                ("is_superuser", True),
                ("idApp", application.ApplicationID),
            ):
                if getattr(user, field) != value:
                    setattr(user, field, value)
                    update_fields.append(field)
            if not password_was_usable and not user.must_change_password:
                user.must_change_password = True
                update_fields.append("must_change_password")
            if update_fields:
                user.save(update_fields=update_fields)

        _, role_created = UserRoles.objects.get_or_create(UserID=user, RoleID=role)

        setup_email_state = "NOT_REQUIRED"
        if not user.has_usable_password():
            send_requested = is_enabled(options["send_setup_email"])
            already_accepted = has_accepted_setup_email(user)
            if send_requested and (options["resend_setup_email"] or not already_accepted):
                try:
                    send_setup_email(user)
                    setup_email_state = "SENT"
                except Exception as exc:
                    raise CommandError(
                        "Super Master ensured, but the setup email failed. "
                        "Review EmailDeliveryLogs and the JobCron email provider."
                    ) from exc
            elif already_accepted:
                setup_email_state = "ALREADY_ACCEPTED"
            else:
                setup_email_state = "DISABLED"

        self.stdout.write(
            self.style.SUCCESS(
                "Super Master ensured: "
                f"email={email}, created={created}, "
                f"password_changed=False, password_usable_before={password_was_usable}, "
                f"role_created={role_created}, setup_email={setup_email_state}"
            )
        )
        if not user.has_usable_password():
            self.stdout.write(
                "Password assignment remains pending until the emailed reset link is completed."
            )
