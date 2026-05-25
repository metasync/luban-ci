import unittest
from unittest.mock import patch

from click.testing import CliRunner

from luban_provisioner.main import cli


class TestProjectDryRun(unittest.TestCase):
    def test_project_dry_run_skips_provider_calls(self):
        class DummyProvider:
            def create_project(self, *args, **kwargs):
                raise AssertionError("create_project should not be called in dry-run")

        runner = CliRunner()

        with patch(
            "luban_provisioner.commands.project.get_git_provider", return_value=DummyProvider()
        ):
            result = runner.invoke(
                cli,
                [
                    "project",
                    "--dry-run",
                    "--project-name",
                    "demo",
                    "--git-organization",
                    "demo-org",
                    "--git-provider",
                    "github",
                    "--git-token",
                    "DUMMY",
                    "--git-server",
                    "github.com",
                ],
            )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Dry run", result.output)


if __name__ == "__main__":
    unittest.main()
