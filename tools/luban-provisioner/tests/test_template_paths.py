import os
import tempfile
import unittest
from unittest.mock import patch

from luban_provisioner.templates.paths import resolve_template_path


class TestTemplatePaths(unittest.TestCase):
    def test_resolve_template_path_returns_existing_path(self):
        with tempfile.TemporaryDirectory() as td:
            existing = os.path.join(td, "template")
            with open(existing, "w", encoding="utf-8"):
                pass

            self.assertEqual(resolve_template_path(existing), existing)

    def test_resolve_template_path_local_fallback_nested(self):
        with tempfile.TemporaryDirectory() as td:
            local_template = os.path.join(td, "tools/luban-provisioner/templates/source/mytpl")
            os.makedirs(local_template, exist_ok=True)

            with patch("os.getcwd", return_value=td):
                resolved = resolve_template_path("/app/templates/source/mytpl")

            self.assertEqual(resolved, local_template)

    def test_resolve_template_path_local_fallback_basename(self):
        with tempfile.TemporaryDirectory() as td:
            local_template = os.path.join(td, "tools/luban-provisioner/templates/mytpl")
            os.makedirs(local_template, exist_ok=True)

            with patch("os.getcwd", return_value=td):
                resolved = resolve_template_path("/app/templates/mytpl")

            self.assertEqual(resolved, local_template)

    def test_resolve_template_path_when_running_in_tool_dir(self):
        with tempfile.TemporaryDirectory() as td:
            tool_dir = os.path.join(td, "tools/luban-provisioner")
            os.makedirs(os.path.join(tool_dir, "src/luban_provisioner"), exist_ok=True)
            local_template = os.path.join(tool_dir, "templates/source/mytpl")
            os.makedirs(local_template, exist_ok=True)

            with patch("os.getcwd", return_value=tool_dir):
                resolved = resolve_template_path("/app/templates/source/mytpl")

            self.assertEqual(resolved, local_template)

    def test_resolve_template_path_not_found_raises(self):
        with tempfile.TemporaryDirectory() as td:
            with (
                patch("os.getcwd", return_value=td),
                patch("click.echo") as echo,
            ):
                with self.assertRaises(FileNotFoundError):
                    resolve_template_path("/app/templates/missing")

            echo.assert_called_once()


if __name__ == "__main__":
    unittest.main()
