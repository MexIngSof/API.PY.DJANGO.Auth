"""Permission grants must not turn user-supplied false strings into True."""
import unittest

from access.permission_flags import parse_permission_allow


class PermissionAllowParsingTests(unittest.TestCase):
    def test_explicit_denial_is_never_truthy(self):
        for value in (False, 0, "false", "False", " FALSE ", "0", "no", "off", "n"):
            with self.subTest(value=value):
                self.assertIs(parse_permission_allow(value), False)

    def test_explicit_allow_and_default(self):
        for value in (True, 1, "true", "TRUE", " 1 ", "yes", "on", "y"):
            with self.subTest(value=value):
                self.assertIs(parse_permission_allow(value), True)

    def test_ambiguous_payloads_fail_closed(self):
        for value in (None, "", "false-ish", "2", 2, -1, [], {}, 1.0):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_permission_allow(value)


if __name__ == "__main__":
    unittest.main()
