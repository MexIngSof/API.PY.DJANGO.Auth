from django.conf import settings
from django.contrib.auth.password_validation import get_default_password_validators
from django.test import SimpleTestCase


class CanonicalPasswordPolicyContractTests(SimpleTestCase):
    def test_minimum_password_length_is_twelve(self):
        validators = get_default_password_validators()
        minimum_length = next(
            validator
            for validator in validators
            if validator.__class__.__name__ == "MinimumLengthValidator"
        )

        self.assertEqual(minimum_length.min_length, 12)

    def test_password_policy_is_centrally_configured(self):
        validator_names = {
            item["NAME"] for item in settings.AUTH_PASSWORD_VALIDATORS
        }

        self.assertIn(
            "django.contrib.auth.password_validation.MinimumLengthValidator",
            validator_names,
        )
        self.assertIn(
            "django.contrib.auth.password_validation.CommonPasswordValidator",
            validator_names,
        )
        self.assertIn(
            "django.contrib.auth.password_validation.NumericPasswordValidator",
            validator_names,
        )
