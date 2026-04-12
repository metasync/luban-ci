import base64
import json
import os
import random
import subprocess
import traceback
from urllib.parse import urlsplit, urlunsplit

import click
from cookiecutter.main import cookiecutter
from ruamel.yaml import YAML


def configure_git_https_auth(git_username, git_token, git_server):
    mode = (os.getenv("GIT_HTTPS_AUTH_MODE") or "credential_store").strip()
    if mode not in {"credential_store", "extraheader_basic"}:
        mode = "credential_store"
    if not git_username:
        git_username = "git"

    os.environ["GIT_TERMINAL_PROMPT"] = "0"

    if mode == "extraheader_basic":
        basic_user = (os.getenv("GIT_BASIC_AUTH_USERNAME") or git_username).strip()
        raw = f"{basic_user}:{git_token}".encode("utf-8")
        basic = base64.b64encode(raw).decode("ascii")
        os.environ["LUBAN_GIT_HTTPS_AUTH_MODE"] = "extraheader_basic"
        os.environ["LUBAN_GIT_AUTH_HEADER"] = f"Authorization: Basic {basic}"
        return

    os.environ["LUBAN_GIT_HTTPS_AUTH_MODE"] = "credential_store"
    os.environ.pop("LUBAN_GIT_AUTH_HEADER", None)

    if git_server and "://" in git_server:
        parts = urlsplit(git_server)
        if parts.netloc:
            git_server = parts.netloc
    git_server = (git_server or "").strip().strip("/")
    subprocess.run(["git", "config", "--global", "credential.helper", "store"], check=True)
    credentials_path = os.path.expanduser("~/.git-credentials")
    with open(credentials_path, "w", encoding="utf-8") as f:
        f.write(f"https://{git_username}:{git_token}@{git_server}\n")


def run_git(args, cwd=None, check=True, capture_output=False, text=True):
    env = os.environ.copy()
    env.setdefault("GIT_TERMINAL_PROMPT", "0")

    cmd = ["git"]
    if env.get("LUBAN_GIT_HTTPS_AUTH_MODE") == "extraheader_basic" and env.get(
        "LUBAN_GIT_AUTH_HEADER"
    ):
        cmd.extend(["--config-env=http.extraHeader=LUBAN_GIT_AUTH_HEADER"])

    cmd.extend(args)
    return subprocess.run(
        cmd, cwd=cwd, env=env, check=check, capture_output=capture_output, text=text
    )


def apply_git_https_config(config: dict, git_provider: str, git_server: str):
    config = config or {}

    env_mode = (os.getenv("GIT_HTTPS_AUTH_MODE") or "").strip()
    env_base_url = (os.getenv("GIT_BASE_URL") or "").strip()
    env_basic_user = (os.getenv("GIT_BASIC_AUTH_USERNAME") or "").strip()

    base_url = env_base_url or config.get(f"{git_provider}_base_url")

    mode = env_mode or config.get(f"{git_provider}_https_auth_mode")
    if not mode:
        mode = "credential_store"
    if str(mode).strip() not in {"credential_store", "extraheader_basic"}:
        mode = "credential_store"

    os.environ["GIT_HTTPS_AUTH_MODE"] = str(mode).strip()

    basic_user = env_basic_user or config.get(f"{git_provider}_basic_auth_username")
    if basic_user is not None and str(basic_user).strip() != "":
        os.environ["GIT_BASIC_AUTH_USERNAME"] = str(basic_user).strip()

    return base_url


def _redact_url(url: str) -> str:
    try:
        parts = urlsplit(url)
        if "@" not in parts.netloc:
            return url
        host = parts.netloc.split("@", 1)[1]
        return urlunsplit((parts.scheme, host, parts.path, parts.query, parts.fragment))
    except Exception:
        return "<redacted>"


def configure_git_identity(user_name="Luban CI", user_email="ci@luban.com"):
    run_git(["config", "--global", "user.email", user_email], check=True)
    run_git(["config", "--global", "user.name", user_name], check=True)
    run_git(["config", "--global", "--add", "safe.directory", "*"], check=True)


def load_config(config_file):
    """
    Load configuration from a YAML or JSON file.
    """
    if not config_file or not os.path.exists(config_file):
        return {}

    try:
        with open(config_file, "r") as f:
            if config_file.endswith(".json"):
                return json.load(f)
            else:
                return YAML(typ="safe").load(f)
    except Exception as e:
        click.echo(f"Error loading config file {config_file}: {e}", err=True)
        return {}


def load_config_from_dir(config_dir):
    """
    Load all config files from a directory and return a merged dict.
    Ignores hidden files.
    This is useful for loading ConfigMaps mounted as volumes.
    """
    config = {}
    if not os.path.exists(config_dir):
        return config

    for filename in os.listdir(config_dir):
        if filename.startswith("..") or filename.startswith("."):
            continue

        file_path = os.path.join(config_dir, filename)
        if os.path.isfile(file_path):
            try:
                with open(file_path, "r") as f:
                    content = f.read().strip()
                    if content:
                        config[filename] = content
            except Exception as e:
                click.echo(f"Warning: Failed to read config file {file_path}: {e}", err=True)
    return config


def render_template(template_path, output_dir, context, overwrite=False):
    """
    Renders a cookiecutter template.
    """
    click.echo(f"Rendering template from {template_path} to {output_dir}...")
    try:
        cookiecutter(
            template_path,
            no_input=True,
            output_dir=output_dir,
            extra_context=context,
            overwrite_if_exists=overwrite,
        )
        click.echo(f"Successfully generated template in {output_dir}")
    except Exception as e:
        click.echo(f"Error generating template: {e}", err=True)
        traceback.print_exc()
        raise e


def clone_git_repo(repo_url, target_dir, user_name="Luban CI", user_email="ci@luban.com"):
    """Clone a git repository to a target directory."""
    try:
        click.echo(f"Cloning {_redact_url(repo_url)} into {target_dir}...")
        run_git(["clone", repo_url, target_dir], check=True)

        # Configure local git user
        cwd = os.getcwd()
        os.chdir(target_dir)
        try:
            run_git(["config", "user.name", user_name], check=True)
            run_git(["config", "user.email", user_email], check=True)
        finally:
            os.chdir(cwd)

    except subprocess.CalledProcessError as e:
        click.echo(f"Git clone failed: {e}", err=True)
        raise e


def commit_and_push(repo_dir, message, branch="main", retries=5):
    """Commit all changes in the repo and push to remote with retry logic."""
    cwd = os.getcwd()
    import time

    try:
        os.chdir(repo_dir)
        click.echo(f"Committing changes in {repo_dir}...")

        # Add all files
        run_git(["add", "."], check=True)

        # Check if there are changes
        status = run_git(["status", "--porcelain"], capture_output=True, text=True, check=False)
        if not status.stdout.strip():
            click.echo("No changes to commit.")
        else:
            # Commit
            run_git(["commit", "-m", message], check=True)

        # Ensure we are on the target branch
        current_branch = run_git(
            ["rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
        if current_branch != branch:
            click.echo(f"Renaming branch {current_branch} to {branch}...")
            run_git(["branch", "-M", branch], check=True)

        # Push with retry
        for i in range(retries):
            try:
                click.echo(f"Pushing to {branch} (Attempt {i + 1}/{retries})...")
                run_git(["push", "origin", branch], check=True)
                click.echo("Push successful.")
                break
            except subprocess.CalledProcessError:
                if i < retries - 1:
                    click.echo("Push failed. Pulling rebase and retrying...")
                    time.sleep(random.uniform(1, 3))  # Random jitter
                    try:
                        run_git(["pull", "--rebase", "origin", branch], check=True)
                    except subprocess.CalledProcessError as e:
                        click.echo(f"Pull rebase failed: {e}. Aborting retry.", err=True)
                        raise e
                else:
                    click.echo("Max retries reached. Push failed.")
                    raise

    except subprocess.CalledProcessError as e:
        click.echo(f"Git commit/push failed: {e}", err=True)
        raise e
    finally:
        os.chdir(cwd)


def initialize_git_repo(
    repo_dir,
    remote_url,
    user_name="Luban CI",
    user_email="luban-ci@metasync.io",
    initial_branch="main",
):
    """Initialize a git repository, commit all files, and push to remote."""
    cwd = os.getcwd()
    try:
        os.chdir(repo_dir)

        click.echo(f"Initializing git repo in {repo_dir}...")

        # Init
        run_git(["init"], check=True)
        run_git(["config", "user.name", user_name], check=True)
        run_git(["config", "user.email", user_email], check=True)
        run_git(["config", "--add", "safe.directory", "*"], check=True)

        # Branch
        run_git(["branch", "-M", initial_branch], check=True)

        # Add and Commit
        run_git(["add", "."], check=True)
        run_git(["commit", "-m", "Initial provisioning"], check=True)

        # Remote
        run_git(["remote", "add", "origin", remote_url], check=True)

        # Push
        click.echo(f"Pushing to {initial_branch}...")
        run_git(["push", "-u", "origin", initial_branch, "--force"], check=True)

    except subprocess.CalledProcessError as e:
        click.echo(f"Git operation failed: {e}", err=True)
        raise e
    finally:
        os.chdir(cwd)


def patch_default_service_account(target_ns, image_pull_secret):
    """
    Deprecated: Patch logic moved to GitOps manifests.
    Keeping function signature for compatibility if needed, but doing nothing.
    """
    pass


def create_and_push_branch(repo_dir, branch_name):
    """Create a new branch and push it."""
    cwd = os.getcwd()
    try:
        os.chdir(repo_dir)
        click.echo(f"Creating and pushing branch {branch_name}...")
        run_git(["checkout", "-b", branch_name], check=True)
        run_git(["push", "-u", "origin", branch_name, "--force"], check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Git branch operation failed: {e}", err=True)
        raise e
    finally:
        os.chdir(cwd)
