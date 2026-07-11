import os

from django.core.management.base import BaseCommand, CommandError

from access.models import Applications
from roles.models import Roles, UserRoles
from user.models import UserAccount


APPLICATION_CODE = "JOBCRON"
ROLE_NAME = "JOBCRON_SUPER_ADMIN"


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

    def handle(self, *args, **options):
        enabled = str(options["enabled"]).lower() in {"true", "1", "yes"}
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

        self.stdout.write(
            self.style.SUCCESS(
                "Super Master ensured: "
                f"email={email}, created={created}, "
                f"password_changed=False, password_usable_before={password_was_usable}, "
                f"role_created={role_created}"
            )
        )
        if not user.has_usable_password():
            self.stdout.write(
                "Password assignment is pending. Use Gateway/Auth password reset flow to send the setup link."
            )
