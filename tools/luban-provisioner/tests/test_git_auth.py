import io
import sys
import types
import unittest
from unittest.mock import patch


class TestGitAuth(unittest.TestCase):
    def test_get_remote_url_never_embeds_token(self):
        if "click" not in sys.modules:
            sys.modules["click"] = types.SimpleNamespace(echo=lambda *args, **kwargs: None)
        if "luban_provisioner.providers.github" not in sys.modules:
            github_mod = types.ModuleType("luban_provisioner.providers.github")
            github_mod.GitHubProvider = object
            sys.modules["luban_provisioner.providers.github"] = github_mod
        if "luban_provisioner.providers.azure" not in sys.modules:
            azure_mod = types.ModuleType("luban_provisioner.providers.azure")
            azure_mod.AzureProvider = object
            sys.modules["luban_provisioner.providers.azure"] = azure_mod
        from luban_provisioner.provider_factory import get_remote_url

        token = "SECRET"
        github_url = get_remote_url("github", token, "github.com", "acme", "ignored", "repo")
        self.assertEqual(github_url, "https://github.com/acme/repo.git")
        self.assertNotIn(token, github_url)
        self.assertNotIn("@", github_url.split("//", 1)[1].split("/", 1)[0])

        github_url2 = get_remote_url(
            "github", token, "https://github.com/", "acme", "ignored", "repo"
        )
        self.assertEqual(github_url2, "https://github.com/acme/repo.git")
        self.assertNotIn(token, github_url2)

        azure_url = get_remote_url("azure", token, "dev.azure.com", "org", "proj", "repo")
        self.assertEqual(azure_url, "https://dev.azure.com/org/proj/_git/repo")
        self.assertNotIn(token, azure_url)

        azure_url2 = get_remote_url("azure", token, "https://dev.azure.com/", "org", "proj", "repo")
        self.assertEqual(azure_url2, "https://dev.azure.com/org/proj/_git/repo")
        self.assertNotIn(token, azure_url2)

    def test_configure_git_https_auth_writes_expected_credentials_line(self):
        if "click" not in sys.modules:
            sys.modules["click"] = types.SimpleNamespace(echo=lambda *args, **kwargs: None)
        if "ruamel" not in sys.modules:
            sys.modules["ruamel"] = types.ModuleType("ruamel")
        if "ruamel.yaml" not in sys.modules:
            ruamel_yaml = types.ModuleType("ruamel.yaml")
            ruamel_yaml.YAML = lambda *args, **kwargs: None
            sys.modules["ruamel.yaml"] = ruamel_yaml
        if "cookiecutter" not in sys.modules:
            sys.modules["cookiecutter"] = types.ModuleType("cookiecutter")
        if "cookiecutter.main" not in sys.modules:
            cookiecutter_main = types.ModuleType("cookiecutter.main")
            cookiecutter_main.cookiecutter = lambda *args, **kwargs: None
            sys.modules["cookiecutter.main"] = cookiecutter_main
        from luban_provisioner.utils import configure_git_https_auth

        writes = {}

        def fake_open(path, mode, encoding=None):
            self.assertEqual(path, "/tmp/.git-credentials")
            self.assertIn("w", mode)
            buffer = io.StringIO()

            original_close = buffer.close

            def capture_close():
                writes["content"] = buffer.getvalue()
                original_close()

            buffer.close = capture_close
            return buffer

        with (
            patch("subprocess.run") as run,
            patch("os.path.expanduser", return_value="/tmp/.git-credentials"),
            patch("builtins.open", new=fake_open),
        ):
            configure_git_https_auth("alice", "TOKEN", "https://dev.azure.com/")

        run.assert_called_once_with(
            ["git", "config", "--global", "credential.helper", "store"], check=True
        )
        self.assertEqual(writes["content"], "https://alice:TOKEN@dev.azure.com\n")


if __name__ == "__main__":
    unittest.main()
