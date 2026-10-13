from pathlib import Path
from unittest import TestCase

ROOT = Path(__file__).resolve().parents[1]
CERTIFIER = ROOT / "scripts" / "certify_erp_client_platform.py"


class SelfHostedCertificationWorkflowContractTests(TestCase):
    def test_owner_certification_is_local_not_github_hosted(self):
        workflow = ROOT / ".github" / "workflows" / "erp-client-platform-v1-self-hosted-certification.yml"
        self.assertFalse(workflow.exists(), "routine certification must not be an active hosted workflow")
        self.assertTrue(CERTIFIER.exists(), "owner-local certifier must remain available")

    def test_owner_certifier_preserves_auth_permission_scope(self):
        self.assertTrue(CERTIFIER.exists(), "owner-local certifier must exist")
        source = CERTIFIER.read_text(encoding="utf-8")
        self.assertIn('run("check")', source)
        self.assertIn('run("makemigrations", "--check", "--dry-run")', source)
        self.assertIn("PostgreSQL 16.15 required", source)
        self.assertIn('run("migrate", "--plan")', source)
        self.assertIn('run("migrate", "--noinput")', source)
        self.assertIn("user.test_database_checks.AuthDatabaseConfigurationCheckTests.test_django_temporary_database_is_allowed_only_during_test_execution", source)
        self.assertIn("access.test_customer_enterprise_permissions", source)
        self.assertIn("access.test_jobcron_product_import_permissions", source)
