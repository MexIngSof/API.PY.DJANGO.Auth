import ast
from pathlib import Path
import unittest
from urllib.parse import parse_qsl, urlparse


ROOT = Path(__file__).resolve().parent
SETTINGS = ROOT / "config" / "settings.py"
ADMIN = ROOT / "user" / "admin.py"


class RuntimeSecretKeyContractTests(unittest.TestCase):
    def _settings_tree(self):
        return ast.parse(SETTINGS.read_text(encoding="utf-8"))

    def _evaluate_secret_key_assignment(self, values):
        tree = self._settings_tree()
        assignment = next(
            node
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "SECRET_KEY" for target in node.targets)
        )
        expression = ast.Expression(assignment.value)
        return eval(compile(expression, str(SETTINGS), "eval"), {"getenv": values.get})

    def _evaluate_database_config(self, values):
        tree = self._settings_tree()
        functions = [
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name in {"_append_search_path", "_configure_auth_search_path", "build_postgres_database_config"}
        ]
        namespace = {
            "getenv": lambda name, default="": values.get(name, default),
            "ImproperlyConfigured": RuntimeError,
            "parse_qsl": parse_qsl,
            "urlparse": urlparse,
        }
        exec(compile(ast.Module(body=functions, type_ignores=[]), str(SETTINGS), "exec"), namespace)
        return namespace["build_postgres_database_config"]()

    def test_docker_runtime_django_secret_key_is_accepted(self):
        self.assertEqual(
            self._evaluate_secret_key_assignment({"DJANGO_SECRET_KEY": "synthetic-runtime-key"}),
            "synthetic-runtime-key",
        )

    def test_legacy_secret_key_remains_a_fallback(self):
        self.assertEqual(
            self._evaluate_secret_key_assignment({"SECRET_KEY": "legacy-local-key"}),
            "legacy-local-key",
        )

    def test_django_secret_key_takes_precedence_when_both_are_set(self):
        self.assertEqual(
            self._evaluate_secret_key_assignment(
                {"DJANGO_SECRET_KEY": "canonical-local-key", "SECRET_KEY": "legacy-local-key"}
            ),
            "canonical-local-key",
        )

    def test_roles_app_is_registered_for_auth_access_models(self):
        assignment = next(
            node
            for node in self._settings_tree().body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "INSTALLED_APPS" for target in node.targets)
        )
        self.assertIn("roles", ast.literal_eval(assignment.value))

    def test_auth_postgres_options_include_both_canonical_schemas(self):
        database = self._evaluate_database_config(
            {"AUTH_POSTGRES_OPTIONS": '-c search_path="Auth","AuthRuntime",public'}
        )
        options = database["OPTIONS"]["options"]
        self.assertIn('"Auth"', options)
        self.assertIn('"AuthRuntime"', options)

    def test_generic_runtime_postgres_options_are_used_when_auth_alias_is_absent(self):
        expected = '-c search_path="Auth","AuthRuntime",public'
        database = self._evaluate_database_config({"POSTGRES_OPTIONS": expected})
        self.assertIn('"Auth"', database["OPTIONS"]["options"])
        self.assertIn('"AuthRuntime"', database["OPTIONS"]["options"])

    def test_auth_db_uses_generic_runtime_connection_variables(self):
        database = self._evaluate_database_config(
            {
                "DB_NAME": "Auth",
                "DB_USER": "Auth",
                "DB_PASSWORD": "synthetic-only-test-password",
                "DB_HOST": "db-postgresql",
                "DB_PORT": "5432",
                "POSTGRES_OPTIONS": '-c search_path="Auth","AuthRuntime",public',
            }
        )
        self.assertEqual(database["HOST"], "db-postgresql")
        self.assertEqual(database["PORT"], "5432")
        self.assertEqual(database["PASSWORD"], "synthetic-only-test-password")
    def test_user_admin_uses_inlines_for_custom_permission_through_models(self):
        tree = ast.parse(ADMIN.read_text(encoding="utf-8"))
        admin_class = next(
            node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "UserAccountAdmin"
        )
        assignments = {
            target.id: node.value
            for node in admin_class.body
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name)
        }
        fieldsets = ast.literal_eval(assignments["fieldsets"])
        field_names = {field for _, section in fieldsets for field in section["fields"]}
        self.assertNotIn("groups", field_names)
        self.assertNotIn("user_permissions", field_names)
        self.assertEqual(ast.literal_eval(assignments["filter_horizontal"]), ())
        self.assertEqual(
            {item.id for item in assignments["inlines"].elts},
            {"UserAccountGroupInline", "UserAccountUserPermissionInline"},
        )


if __name__ == "__main__":
    unittest.main()
