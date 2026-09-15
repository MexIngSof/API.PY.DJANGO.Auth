from pathlib import Path
from unittest import TestCase

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "erp-client-platform-v1-self-hosted-certification.yml"
CERTIFIER = ROOT / "scripts" / "certify_erp_client_platform.py"


class SelfHostedCertificationWorkflowContractTests(TestCase):
    def test_workflow_is_controlled_self_hosted_and_postgresql_14_4(self):
        self.assertTrue(WORKFLOW.exists(), "self-hosted certification workflow must exist")
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", source)
        self.assertIn("push:", source)
        self.assertIn("feature/erp-client-platform-v1", source)
        self.assertIn("[self-hosted-cert]", source)
        self.assertIn("github.event_name == 'workflow_dispatch'", source)
        self.assertIn("contains(github.event.head_commit.message", source)
        self.assertIn("runs-on: [self-hosted, linux, x64]", source)
        self.assertIn("image: postgres:14.4", source)
        self.assertIn("actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09", source)
        self.assertIn("actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1", source)
        self.assertIn("python scripts/certify_erp_client_platform.py", source)
        self.assertNotIn("ubuntu-latest", source)
        self.assertNotIn("ubuntu-24.04", source)

    def test_owner_certifier_preserves_auth_permission_scope(self):
        self.assertTrue(CERTIFIER.exists(), "owner-local certifier must exist")
        source = CERTIFIER.read_text(encoding="utf-8")
        self.assertIn('run("check")', source)
        self.assertIn('run("makemigrations", "--check", "--dry-run")', source)
        self.assertIn("PostgreSQL 14.4 required", source)
        self.assertIn('run("migrate", "--plan")', source)
        self.assertIn('run("migrate", "--noinput")', source)
        self.assertIn("user.test_database_checks.AuthDatabaseConfigurationCheckTests.test_django_temporary_database_is_allowed_only_during_test_execution", source)
        self.assertIn("access.test_customer_enterprise_permissions", source)
        self.assertIn("access.test_jobcron_product_import_permissions", source)
