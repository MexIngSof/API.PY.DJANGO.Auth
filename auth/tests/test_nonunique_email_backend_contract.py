from unittest.mock import patch

from django.contrib.auth.backends import ModelBackend
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.tokens import RefreshToken

from access.models import Applications
from user.models import UserAccount
from user.serializers import ApplicationScopedTokenObtainPairSerializer


class NonUniqueEmailBackendContractTests(TestCase):
    def setUp(self):
        self.refapart, _ = Applications.objects.get_or_create(
            Code="REFAPART", defaults={"Name": "RefaPart", "IsActive": True}
        )
        self.jobcron, _ = Applications.objects.get_or_create(
            Code="JOBCRON", defaults={"Name": "JobCron", "IsActive": True}
        )
        self.refapart_user = UserAccount.objects.create_user(
            email="shared@example.test",
            password="refapart-password",
            first_name="Refa",
            last_name="Part",
            idApp=self.refapart.ApplicationID,
            is_active=True,
        )
        self.jobcron_user = UserAccount.objects.create_user(
            email="shared@example.test",
            password="jobcron-password",
            first_name="Job",
            last_name="Cron",
            idApp=self.jobcron.ApplicationID,
            is_active=True,
        )

    def test_scoped_jwt_login_selects_the_account_for_the_requested_application(self):
        request = APIRequestFactory().post(
            "/api/auth/jwt/create/",
            {"email": "SHARED@example.test", "password": "refapart-password"},
            format="json",
        )
        serializer = ApplicationScopedTokenObtainPairSerializer(
            data={"email": "SHARED@example.test", "password": "refapart-password"},
            context={"request": request},
        )

        with patch(
            "user.serializers.resolve_application_context",
            return_value=self.refapart,
        ):
            serializer.is_valid(raise_exception=True)

        self.assertEqual(serializer.user.pk, self.refapart_user.pk)
        self.assertNotEqual(serializer.user.pk, self.jobcron_user.pk)
        refresh = RefreshToken(serializer.validated_data["refresh"])
        self.assertEqual(refresh["user_id"], self.refapart_user.pk)
        self.assertEqual(refresh["application_id"], self.refapart.ApplicationID)
        self.assertEqual(refresh["application_code"], "REFAPART")

    def test_unscoped_model_backend_cannot_resolve_duplicate_application_emails(self):
        self.assertEqual(
            UserAccount.objects.filter(email__iexact="shared@example.test").count(),
            2,
        )

        with self.assertRaises(UserAccount.MultipleObjectsReturned):
            ModelBackend().authenticate(
                request=None,
                username="shared@example.test",
                password="refapart-password",
            )
