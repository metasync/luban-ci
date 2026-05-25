import os
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from luban_provisioner.main import cli


class TestInfraDryRunDir(unittest.TestCase):
    def test_infra_ci_update_respects_dry_run_dir(self):
        runner = CliRunner()

        with runner.isolated_filesystem():
            out_dir = os.path.abspath("out")
            os.makedirs(out_dir, exist_ok=True)

            rendered = {}

            def fake_render(template_path, output_dir, context, overwrite=False):
                rendered["output_dir"] = output_dir
                os.makedirs(output_dir, exist_ok=True)

            with (
                patch(
                    "luban_provisioner.commands.infra.resolve_template_path",
                    return_value="/tmp/tpl",
                ),
                patch("luban_provisioner.commands.infra.render_template", side_effect=fake_render),
            ):
                result = runner.invoke(
                    cli,
                    [
                        "infra",
                        "ci",
                        "update",
                        "--dry-run",
                        "--dry-run-dir",
                        out_dir,
                        "--repo-name",
                        "demo-infra-ci",
                        "--project-name",
                        "demo",
                        "--git-provider",
                        "github",
                        "--git-token",
                        "DUMMY",
                        "--git-server",
                        "github.com",
                        "--admin-group",
                        "demo-admin",
                        "--developer-group",
                        "demo-dev",
                    ],
                )

            self.assertEqual(result.exit_code, 0)
            self.assertIn("Dry run", result.output)
            self.assertEqual(
                rendered["output_dir"],
                os.path.join(out_dir, "demo-infra-ci", "overlays"),
            )


if __name__ == "__main__":
    unittest.main()
