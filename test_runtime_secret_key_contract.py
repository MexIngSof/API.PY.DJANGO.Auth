import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent
SETTINGS = ROOT / "config" / "settings.py"


class RuntimeSecretKeyContractTests(unittest.TestCase):
    def _evaluate_secret_key_assignment(self, values):
        tree = ast.parse(SETTINGS.read_text(encoding="utf-8"))
        assignment = next(
            node
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "SECRET_KEY" for target in node.targets)
        )
        expression = ast.Expression(assignment.value)
        return eval(compile(expression, str(SETTINGS), "eval"), {"getenv": values.get})

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


if __name__ == "__main__":
    unittest.main()
