from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from user.database_checks import auth_database_configuration_check


class AuthDatabaseConfigurationCheckTests(SimpleTestCase):
    @override_settings(
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "Auth",
                "USER": "Auth",
                "OPTIONS": {"options": '-c search_path="Auth","AuthRuntime",public'},
            }
        }
    )
    def test_canonical_configuration_has_no_errors(self):
        self.assertEqual(auth_database_configuration_check(None), [])

    @override_settings(
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "test_Auth",
                "USER": "Auth",
                "OPTIONS": {"options": '-c search_path=public,"Auth","AuthRuntime"'},
            }
        }
    )
    def test_django_temporary_database_is_allowed_only_during_test_execution(self):
        with patch("user.database_checks.sys.argv", ["manage.py", "test", "user.test_database_checks"]):
            self.assertEqual(auth_database_configuration_check(None), [])

    @override_settings(
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "test_Auth",
                "USER": "Auth",
                "OPTIONS": {"options": '-c search_path="Auth","AuthRuntime",public'},
            }
        }
    )
    def test_temporary_database_name_is_rejected_outside_test_execution(self):
        with patch("user.database_checks.sys.argv", ["manage.py", "check"]):
            errors = auth_database_configuration_check(None)
        self.assertIn("auth.E002", {error.id for error in errors})

    @override_settings(
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "Auth",
                "USER": "auth_user",
                "OPTIONS": {"options": '-c search_path="Auth","AuthRuntime",public'},
            }
        }
    )
    def test_legacy_user_is_rejected(self):
        errors = auth_database_configuration_check(None)
        self.assertIn("auth.E003", {error.id for error in errors})

    @override_settings(
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": "Auth",
                "USER": "Auth",
                "OPTIONS": {},
            }
        }
    )
    def test_sqlite_and_missing_schemas_are_rejected(self):
        errors = auth_database_configuration_check(None)
        ids = {error.id for error in errors}
        self.assertIn("auth.E001", ids)
        self.assertIn("auth.E004", ids)
