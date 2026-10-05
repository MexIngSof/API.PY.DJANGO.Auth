import json

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from django.db.models.functions import Lower

from access.models import Applications


class Command(BaseCommand):
    help = "Read-only preflight for the ApplicationId + lower(email) identity migration."

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", dest="as_json")

    def handle(self, *args, **options):
        User = get_user_model()
        active_application_ids = set(
            Applications.objects.filter(IsActive=True).values_list("ApplicationID", flat=True)
        )
        user_application_ids = set(User.objects.values_list("idApp", flat=True))
        orphan_application_ids = sorted(
            application_id
            for application_id in user_application_ids
            if application_id not in active_application_ids
        )

        duplicate_groups = list(
            User.objects.annotate(normalized_email=Lower("email"))
            .values("idApp", "normalized_email")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
            .order_by("idApp", "normalized_email")
        )
        non_normalized_ids = list(
            User.objects.exclude(email=Lower("email"))
            .values_list("id", flat=True)
            .order_by("id")
        )

        report = {
            "orphan_application_ids": orphan_application_ids,
            "duplicate_application_email_groups": duplicate_groups,
            "non_normalized_user_ids": non_normalized_ids,
            "safe_for_application_email_constraint": not (
                orphan_application_ids or duplicate_groups or non_normalized_ids
            ),
        }

        if options["as_json"]:
            self.stdout.write(json.dumps(report, sort_keys=True, default=str))
        else:
            self.stdout.write(f"orphan_application_ids={orphan_application_ids}")
            self.stdout.write(f"duplicate_application_email_groups={duplicate_groups}")
            self.stdout.write(f"non_normalized_user_ids={non_normalized_ids}")

        if not report["safe_for_application_email_constraint"]:
            raise CommandError(
                "Task 5 preflight failed; repair orphan, duplicate, or non-normalized identities before migration."
            )

        self.stdout.write(self.style.SUCCESS("Task 5 identity migration preflight passed."))
