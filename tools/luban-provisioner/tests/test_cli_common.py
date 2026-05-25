import unittest
from unittest.mock import patch

from luban_provisioner.cli.common import (
    format_context_for_log,
    mask_sensitive_context,
    parse_set_overrides,
)


class TestCliCommon(unittest.TestCase):
    def test_parse_set_overrides_parses_and_warns(self):
        with patch("click.echo") as echo:
            overrides = parse_set_overrides(["a=1", "bad", "b=two=2"])

        self.assertEqual(overrides, {"a": "1", "b": "two=2"})
        echo.assert_called_once()

    def test_mask_sensitive_context_masks_values(self):
        ctx = {
            "git_token": "abcdef",
            "password": "1234",
            "nested": {"apiKey": "zzzzzz", "x": "y"},
            "list": [{"secret": "hello"}],
        }

        masked = mask_sensitive_context(ctx)

        self.assertEqual(masked["git_token"], "ab**ef")
        self.assertEqual(masked["password"], "****")
        self.assertEqual(masked["nested"]["apiKey"], "zz**zz")
        self.assertEqual(masked["nested"]["x"], "y")
        self.assertEqual(masked["list"][0]["secret"], "he*lo")

    def test_format_context_for_log_respects_env(self):
        ctx = {"token": "abcdef", "x": "y"}

        with patch.dict("os.environ", {"LUBAN_PROVISIONER_LOG_CONTEXT": "0"}, clear=False):
            self.assertIsNone(format_context_for_log(ctx))

        with patch.dict(
            "os.environ",
            {"LUBAN_PROVISIONER_LOG_CONTEXT": "1", "LUBAN_PROVISIONER_MASK_CONTEXT_SECRETS": "0"},
            clear=False,
        ):
            formatted = format_context_for_log(ctx)
            self.assertIn("keys", formatted)
            self.assertIn("token", formatted["sensitive"])
            self.assertEqual(formatted["sensitive"]["token"], "abcdef")

        with patch.dict(
            "os.environ",
            {"LUBAN_PROVISIONER_LOG_CONTEXT": "1", "LUBAN_PROVISIONER_MASK_CONTEXT_SECRETS": "1"},
            clear=False,
        ):
            formatted = format_context_for_log(ctx)
            self.assertIn("keys", formatted)
            self.assertIn("token", formatted["sensitive"])
            self.assertNotEqual(formatted["sensitive"]["token"], "abcdef")


if __name__ == "__main__":
    unittest.main()
