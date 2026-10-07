from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts" / "ci" / "local-validate.ps1"
CERTIFIER = ROOT / "scripts" / "certify_erp_client_platform.py"


class LocalValidateSourceReferenceTests(unittest.TestCase):
    def test_validator_covers_all_application_email_and_global_identity_migrations(self):
        source = VALIDATOR.read_text(encoding="utf-8")
        required_migrations = (
            "user/migrations/0006_application_scoped_email_identity.py",
            "user/migrations/0007_drop_global_email_uniqueness.py",
            "user/migrations/0008_case_insensitive_application_email.py",
            "access/migrations/0039_global_identity_correlation.py",
            "access/migrations/0041_merge_global_identity_and_permission_seeds.py",
        )

        for migration in required_migrations:
            with self.subTest(migration=migration):
                self.assertTrue((ROOT / migration).is_file(), f"migration missing: {migration}")
                self.assertIn(f"'{migration}'", source, f"owner validator omits {migration}")

    def test_validator_runs_the_postgres_case_insensitive_identity_constraint(self):
        source = VALIDATOR.read_text(encoding="utf-8")
        self.assertIn("auth/tests/test_application_email_identity_constraint.py", source)
        self.assertIn("auth.tests.test_application_email_identity_constraint", source)

    def test_all_django_test_commands_reuse_the_local_test_database(self):
        source = VALIDATOR.read_text(encoding="utf-8")
        test_commands = re.findall(r"python manage\.py test ([^;}\r\n]+)", source)

        self.assertTrue(test_commands, "owner validator must declare Django test commands")
        for command in test_commands:
            with self.subTest(command=command):
                self.assertIn("--keepdb", command)

    def test_validator_uses_windows_loopback_for_local_postgresql_by_default(self):
        source = VALIDATOR.read_text(encoding="utf-8")

        self.assertIn("IsOSPlatform", source)
        self.assertIn("OSPlatform]::Windows", source)
        self.assertIn("$env:AUTH_DB_HOST='127.0.0.1'", source)

    def test_postgres_certifier_reuses_the_local_test_database(self):
        source = CERTIFIER.read_text(encoding="utf-8")
        test_call = re.search(r'run\(\s*"test",(.*?)\n\s*\)', source, re.DOTALL)

        self.assertIsNotNone(test_call, "PostgreSQL certifier must declare its focused tests")
        self.assertIn('"--keepdb"', test_call.group(1))

    def test_static_files_and_focused_test_modules_exist(self):
        source = VALIDATOR.read_text(encoding="utf-8")
        file_block = re.search(r"foreach\(\$file in @\((.*?)\)\)", source, re.DOTALL)
        self.assertIsNotNone(file_block, "local validator must declare its static file contract")
        static_paths = re.findall(r"'([^']+)'", file_block.group(1))
        missing_files = [path for path in static_paths if not (ROOT / path).is_file()]

        focused_modules = []
        for command in re.findall(r"python manage\.py test ([^;}\r\n]+)", source):
            focused_modules.extend(token for token in command.split() if not token.startswith("-") and not token.isdigit())
        missing_modules = [
            module
            for module in focused_modules
            if not (ROOT / (module.replace(".", "/") + ".py")).is_file()
        ]
        self.assertEqual(missing_files, [], f"static contract paths do not exist: {missing_files}")
        self.assertEqual(missing_modules, [], f"focused test modules do not exist: {missing_modules}")
        settings = (ROOT / "config" / "settings.py").read_text(encoding="utf-8")
        self.assertIn("search_path={search_path}", settings)
        self.assertIn("_append_search_path(options,", settings)
        self.assertIn('"Auth","AuthRuntime",public', settings)
        self.assertIn("[\\s\\S]*?AuthRuntime", source)
        self.assertIn("$scopedRbac=Get-Content access/scoped_rbac_views.py", source)


if __name__ == "__main__":
    unittest.main()
