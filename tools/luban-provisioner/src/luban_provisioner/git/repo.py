import os
import random
import subprocess

import click

from luban_provisioner.git.exec import redact_url, run_git


def configure_git_identity(user_name="Luban CI", user_email="ci@luban.com"):
    run_git(["config", "--global", "user.email", user_email], check=True)
    run_git(["config", "--global", "user.name", user_name], check=True)
    run_git(["config", "--global", "--add", "safe.directory", "*"], check=True)


def clone_git_repo(repo_url, target_dir, user_name="Luban CI", user_email="ci@luban.com"):
    try:
        click.echo(f"Cloning {redact_url(repo_url)} into {target_dir}...")
        run_git(["clone", repo_url, target_dir], check=True)

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
    cwd = os.getcwd()
    import time

    try:
        os.chdir(repo_dir)
        click.echo(f"Committing changes in {repo_dir}...")

        run_git(["add", "."], check=True)

        status = run_git(["status", "--porcelain"], capture_output=True, text=True, check=False)
        if not status.stdout.strip():
            click.echo("No changes to commit.")
        else:
            run_git(["commit", "-m", message], check=True)

        current_branch = run_git(
            ["rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
        if current_branch != branch:
            click.echo(f"Renaming branch {current_branch} to {branch}...")
            run_git(["branch", "-M", branch], check=True)

        for i in range(retries):
            try:
                click.echo(f"Pushing to {branch} (Attempt {i + 1}/{retries})...")
                run_git(["push", "origin", branch], check=True)
                click.echo("Push successful.")
                break
            except subprocess.CalledProcessError:
                if i < retries - 1:
                    click.echo("Push failed. Pulling rebase and retrying...")
                    time.sleep(random.uniform(1, 3))
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
    cwd = os.getcwd()
    try:
        os.chdir(repo_dir)

        click.echo(f"Initializing git repo in {repo_dir}...")

        run_git(["init"], check=True)
        run_git(["config", "user.name", user_name], check=True)
        run_git(["config", "user.email", user_email], check=True)
        run_git(["config", "--add", "safe.directory", "*"], check=True)

        run_git(["branch", "-M", initial_branch], check=True)

        run_git(["add", "."], check=True)
        run_git(["commit", "-m", "Initial provisioning"], check=True)

        run_git(["remote", "add", "origin", remote_url], check=True)

        click.echo(f"Pushing to {initial_branch}...")
        run_git(["push", "-u", "origin", initial_branch, "--force"], check=True)

    except subprocess.CalledProcessError as e:
        click.echo(f"Git operation failed: {e}", err=True)
        raise e
    finally:
        os.chdir(cwd)


def patch_default_service_account(target_ns, image_pull_secret):
    pass


def create_and_push_branch(repo_dir, branch_name):
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
