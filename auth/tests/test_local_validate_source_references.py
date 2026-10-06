from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts" / "ci" / "local-validate.ps1"


class LocalValidateSourceReferenceTests(unittest.TestCase):
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
