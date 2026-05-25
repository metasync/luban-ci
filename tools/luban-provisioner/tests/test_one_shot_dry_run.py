import os
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from luban_provisioner.main import cli


class TestOneShotDryRun(unittest.TestCase):
    def test_one_shot_dry_run_renders_expected_dirs(self):
        runner = CliRunner()

        with runner.isolated_filesystem():
            output_dir = os.path.abspath("out")
            dummy_template_dir = os.path.abspath("dummy-template")
            os.makedirs(dummy_template_dir, exist_ok=True)

            def fake_source_render(template_path, output_dir, context, overwrite=False):
                app_name = (context or {}).get("app_name") or "app"
                os.makedirs(os.path.join(output_dir, app_name), exist_ok=True)

            def fake_gitops_render(template_path, output_dir, context, overwrite=False):
                app_name = (context or {}).get("app_name") or "app"
                os.makedirs(os.path.join(output_dir, f"{app_name}-gitops"), exist_ok=True)

            def fake_infra_render(template_path, output_dir, context, overwrite=False):
                os.makedirs(output_dir, exist_ok=True)

            with (
                patch(
                    "luban_provisioner.commands.source.resolve_template_path",
                    return_value=dummy_template_dir,
                ),
                patch(
                    "luban_provisioner.commands.gitops.resolve_template_path",
                    return_value=dummy_template_dir,
                ),
                patch(
                    "luban_provisioner.commands.infra.resolve_template_path",
                    return_value=dummy_template_dir,
                ),
                patch(
                    "luban_provisioner.commands.source.render_template",
                    side_effect=fake_source_render,
                ),
                patch(
                    "luban_provisioner.commands.gitops.render_template",
                    side_effect=fake_gitops_render,
                ),
                patch(
                    "luban_provisioner.commands.infra.render_template",
                    side_effect=fake_infra_render,
                ),
            ):
                result = runner.invoke(
                    cli,
                    [
                        "dry-run",
                        "--output-dir",
                        output_dir,
                        "--project-name",
                        "demo",
                        "--application-name",
                        "demo-app",
                        "--git-server",
                        "github.com",
                        "--git-token",
                        "DUMMY",
                    ],
                )

            self.assertEqual(result.exit_code, 0, result.output)

            self.assertTrue(os.path.isdir(os.path.join(output_dir, "demo-app")))
            self.assertTrue(os.path.isdir(os.path.join(output_dir, "demo-app-gitops")))
            self.assertTrue(os.path.isdir(os.path.join(output_dir, "infra-ci-base")))
            self.assertTrue(
                os.path.isdir(
                    os.path.join(output_dir, "infra-ci-overlay", "luban-infra-ci", "overlays")
                )
            )
            self.assertTrue(os.path.isdir(os.path.join(output_dir, "infra-cd-base")))
            self.assertTrue(
                os.path.isdir(
                    os.path.join(output_dir, "infra-cd-overlay", "luban-infra-cd", "overlays")
                )
            )


if __name__ == "__main__":
    unittest.main()
