import subprocess
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from luban_provisioner.main import cli


class TestPromoteDryRun(unittest.TestCase):
    def test_promote_dry_run_skips_push_and_pr(self):
        class DummyProvider:
            def create_pull_request(self, *args, **kwargs):
                raise AssertionError("create_pull_request should not be called in dry-run")

        runner = CliRunner()

        def fake_run_git(args, cwd=None, check=True, capture_output=False, text=True):
            if args[:2] == ["clone", "-b"]:
                raise subprocess.CalledProcessError(returncode=1, cmd=["git"] + args)
            raise AssertionError(f"Unexpected git invocation in dry-run test: {args}")

        with (
            patch(
                "luban_provisioner.commands.promote.get_git_provider", return_value=DummyProvider()
            ),
            patch("luban_provisioner.commands.promote.run_git", side_effect=fake_run_git),
        ):
            result = runner.invoke(
                cli,
                [
                    "promote",
                    "--dry-run",
                    "--app-name",
                    "demo-app",
                    "--git-organization",
                    "demo-org",
                    "--git-provider",
                    "github",
                    "--git-token",
                    "DUMMY",
                    "--git-server",
                    "github.com",
                    "--project-name",
                    "demo",
                ],
            )

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Failed to clone repository", result.output)


if __name__ == "__main__":
    unittest.main()
