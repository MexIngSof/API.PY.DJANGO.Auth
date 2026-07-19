import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from access.models import Applications, ApplicationRoles
from roles.models import Roles, UserRoles
from user.models import UserAccount


E2E_USERS = (
    {
        "app": "JOBCRON",
        "email_env": "AUTH_E2E_JOBCRON_ADMIN_USER",
        "password_env": "AUTH_E2E_JOBCRON_ADMIN_PASSWORD",
        "default_email": "auth-e2e-jobcron-admin@example.local",
        "role": "JOBCRON_SUPER_ADMIN",
        "first_name": "E2E",
        "last_name": "JobCron Admin",
        "staff": True,
        "superuser": False,
    },
    {
        "app": "JOBCRON",
        "email_env": "AUTH_E2E_JOBCRON_LIMITED_USER",
        "password_env": "AUTH_E2E_JOBCRON_LIMITED_PASSWORD",
        "default_email": "auth-e2e-jobcron-limited@example.local",
        "role": "JOBCRON_SUPPORT_ADMIN",
        "first_name": "E2E",
        "last_name": "JobCron Limited",
        "staff": True,
        "superuser": False,
    },
    {
        "app": "REFAPART",
        "email_env": "AUTH_E2E_REFAPART_CUSTOMER_USER",
        "password_env": "AUTH_E2E_REFAPART_CUSTOMER_PASSWORD",
        "default_email": "auth-e2e-refapart-customer@example.local",
        "role": "REFAPART_CUSTOMER",
        "first_name": "E2E",
        "last_name": "RefaPart Customer",
        "staff": False,
        "superuser": False,
    },
    {
        "app": "REFAPART",
        "email_env": "AUTH_E2E_REFAPART_ADMIN_USER",
        "password_env": "AUTH_E2E_REFAPART_ADMIN_PASSWORD",
        "default_email": "auth-e2e-refapart-admin@example.local",
        "role": "REFAPART_ADMIN",
        "first_name": "E2E",
        "last_name": "RefaPart Admin",
        "staff": True,
        "superuser": False,
    },
    {
        "app": "LEXNOVA",
        "email_env": "AUTH_E2E_LEXNOVA_USER",
        "password_env": "AUTH_E2E_LEXNOVA_PASSWORD",
        "default_email": "auth-e2e-lexnova-user@example.local",
        "role": "CUSTOMER",
        "first_name": "E2E",
        "last_name": "LexNova User",
        "staff": False,
        "superuser": False,
    },
    {
        "app": "MEXINGSOF",
        "email_env": "AUTH_E2E_MEXINGSOF_USER",
        "password_env": "AUTH_E2E_MEXINGSOF_PASSWORD",
        "default_email": "auth-e2e-mexingsof-user@example.local",
        "role": "CUSTOMER",
        "first_name": "E2E",
        "last_name": "MexIngSof User",
        "staff": False,
        "superuser": False,
    },
    {
        "app": "TECNOTELEC",
        "email_env": "AUTH_E2E_TECNOTELEC_USER",
        "password_env": "AUTH_E2E_TECNOTELEC_PASSWORD",
        "default_email": "auth-e2e-tecnotelec-user@example.local",
        "role": "CUSTOMER",
        "first_name": "E2E",
        "last_name": "TecnoTelec User",
        "staff": False,
        "superuser": False,
    },
)


class Command(BaseCommand):
    help = "Seeds synthetic Auth users for local/DEV E2E tests without printing secrets."

    def add_arguments(self, parser):
        parser.add_argument(
            "--applications",
            default=os.getenv("AUTH_E2E_APPLICATIONS", ""),
            help="Comma-separated application codes. Defaults to all configured E2E users.",
        )
        parser.add_argument(
            "--password-env",
            default="AUTH_E2E_DEFAULT_PASSWORD",
            help="Fallback password environment variable. Defaults to AUTH_E2E_DEFAULT_PASSWORD.",
        )

    def handle(self, *args, **options):
        if not settings.DEVELOPMENT_MODE and os.getenv("AUTH_E2E_ALLOW_NON_LOCAL", "").lower() not in {
            "true",
            "1",
            "yes",
        }:
            raise CommandError(
                "seed_auth_e2e_users is blocked outside local/DEV. "
                "Set DEVELOPMENT_MODE=True or AUTH_E2E_ALLOW_NON_LOCAL=true only in staging."
            )

        selected = {
            value.strip().upper()
            for value in (options["applications"] or "").split(",")
            if value.strip()
        }
        fallback_password = os.getenv(options["password_env"], "")
        missing_password_vars = []
        seeded = []

        for spec in E2E_USERS:
            if selected and spec["app"] not in selected:
                continue

            password = os.getenv(spec["password_env"], fallback_password)
            if not password:
                missing_password_vars.append(spec["password_env"])
                continue

            application, _ = Applications.objects.update_or_create(
                Code=spec["app"],
                defaults={
                    "Name": spec["app"].replace("_", " ").title(),
                    "Description": f"Aplicacion {spec['app']} para pruebas E2E Auth.",
                    "IsActive": True,
                },
            )
            role, _ = Roles.objects.update_or_create(
                Name=spec["role"],
                defaults={
                    "DisplayName": spec["role"].replace("_", " ").title(),
                    "Description": f"Rol sintetico para pruebas E2E {spec['app']}.",
                },
            )
            ApplicationRoles.objects.get_or_create(ApplicationID=application, RoleID=role)

            email = os.getenv(spec["email_env"], spec["default_email"]).strip().lower()
            user = UserAccount.objects.filter(email=email).first()
            created = user is None
            if created:
                user = UserAccount(email=email)

            user.first_name = spec["first_name"]
            user.last_name = spec["last_name"]
            user.is_active = True
            user.is_staff = spec["staff"]
            user.is_superuser = spec["superuser"]
            user.must_change_password = False
            user.idApp = application.ApplicationID
            user.set_password(password)
            user.save()
            UserRoles.objects.get_or_create(UserID=user, RoleID=role)

            seeded.append((spec["app"], email, spec["role"], created))

        if missing_password_vars:
            raise CommandError(
                "Missing E2E password variables: "
                + ", ".join(sorted(set(missing_password_vars)))
                + f". Or set {options['password_env']} as a local fallback."
            )

        for app, email, role, created in seeded:
            self.stdout.write(
                self.style.SUCCESS(
                    f"E2E user ready: app={app}, email={email}, role={role}, created={created}, password_set=True"
                )
            )
