import subprocess
import click
import os
import traceback
import random
from ruamel.yaml import YAML
import json
from cookiecutter.main import cookiecutter


def configure_git_https_auth(git_token, git_server):
    subprocess.run(["git", "config", "--global", "credential.helper", "store"], check=True)
    credentials_path = os.path.expanduser("~/.git-credentials")
    with open(credentials_path, "w", encoding="utf-8") as f:
        f.write(f"https://git:{git_token}@{git_server}\n")


def configure_git_identity(user_name="Luban CI", user_email="ci@luban.com"):
    subprocess.run(["git", "config", "--global", "user.email", user_email], check=True)
    subprocess.run(["git", "config", "--global", "user.name", user_name], check=True)
    subprocess.run(["git", "config", "--global", "--add", "safe.directory", "*"], check=True)


def load_config(config_file):
    """
    Load configuration from a YAML or JSON file.
    """
    if not config_file or not os.path.exists(config_file):
        return {}
        
    try:
        with open(config_file, 'r') as f:
            if config_file.endswith('.json'):
                return json.load(f)
            else:
                return YAML(typ='safe').load(f)
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
        if filename.startswith('..') or filename.startswith('.'):
            continue
            
        file_path = os.path.join(config_dir, filename)
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'r') as f:
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
            overwrite_if_exists=overwrite
        )
        click.echo(f"Successfully generated template in {output_dir}")
    except Exception as e:
        click.echo(f"Error generating template: {e}", err=True)
        traceback.print_exc()
        raise e

def clone_git_repo(repo_url, target_dir, user_name="Luban CI", user_email="ci@luban.com"):
    """Clone a git repository to a target directory."""
    try:
        click.echo(f"Cloning {repo_url} into {target_dir}...")
        subprocess.run(["git", "clone", repo_url, target_dir], check=True)

        # Configure local git user
        cwd = os.getcwd()
        os.chdir(target_dir)
        try:
            subprocess.run(["git", "config", "user.name", user_name], check=True)
            subprocess.run(["git", "config", "user.email", user_email], check=True)
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
        subprocess.run(["git", "add", "."], check=True)

        # Check if there are changes
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
            click.echo("No changes to commit.")
        else:
            # Commit
            subprocess.run(["git", "commit", "-m", message], check=True)

        # Ensure we are on the target branch
        current_branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True).stdout.strip()
        if current_branch != branch:
            click.echo(f"Renaming branch {current_branch} to {branch}...")
            subprocess.run(["git", "branch", "-M", branch], check=True)

        # Push with retry
        for i in range(retries):
            try:
                click.echo(f"Pushing to {branch} (Attempt {i+1}/{retries})...")
                subprocess.run(["git", "push", "origin", branch], check=True)
                click.echo("Push successful.")
                break
            except subprocess.CalledProcessError:
                if i < retries - 1:
                    click.echo(f"Push failed. Pulling rebase and retrying...")
                    time.sleep(random.uniform(1, 3)) # Random jitter
                    try:
                        subprocess.run(["git", "pull", "--rebase", "origin", branch], check=True)
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

def initialize_git_repo(repo_dir, remote_url, user_name="Luban CI", user_email="luban-ci@metasync.io", initial_branch="main"):
    """Initialize a git repository, commit all files, and push to remote."""
    cwd = os.getcwd()
    try:
        os.chdir(repo_dir)
        
        click.echo(f"Initializing git repo in {repo_dir}...")
        
        # Init
        subprocess.run(["git", "init"], check=True)
        subprocess.run(["git", "config", "user.name", user_name], check=True)
        subprocess.run(["git", "config", "user.email", user_email], check=True)
        subprocess.run(["git", "config", "--add", "safe.directory", "*"], check=True)
        
        # Branch
        subprocess.run(["git", "branch", "-M", initial_branch], check=True)
        
        # Add and Commit
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Initial provisioning"], check=True)
        
        # Remote
        subprocess.run(["git", "remote", "add", "origin", remote_url], check=True)
        
        # Push
        click.echo(f"Pushing to {initial_branch}...")
        subprocess.run(["git", "push", "-u", "origin", initial_branch, "--force"], check=True)
        
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
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)
        subprocess.run(["git", "push", "-u", "origin", branch_name, "--force"], check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Git branch operation failed: {e}", err=True)
        raise e
    finally:
        os.chdir(cwd)
