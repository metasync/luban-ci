import os
import shutil
import sys

import click

from luban_provisioner.provider_factory import get_git_provider, get_remote_url
from luban_provisioner.utils import (
    clone_git_repo,
    commit_and_push,
    configure_git_https_auth,
    configure_git_identity,
    initialize_git_repo,
    render_template,
)


@click.group(name="infra")
def infra():
    """Infrastructure management commands."""
    pass


@infra.group(name="ci")
def ci():
    """CI Infrastructure commands."""
    pass


@infra.group(name="cd")
def cd():
    """CD Infrastructure commands."""
    pass


# --- Helper Functions ---


def _update_impl(
    template_path,
    context,
    repo_name,
    project_name,
    env_name,
    git_organization,
    git_provider,
    git_server,
    git_base_url,
    git_username,
    git_token,
    work_dir,
    infra_project_name,
    local_dir=None,
):
    # Fallback for local template
    if not os.path.exists(template_path):
        cwd = os.getcwd()
        # template_path passed in might be absolute /app/..., try to find local relative
        template_dirname = os.path.basename(template_path)
        local_template = os.path.join(cwd, f"tools/luban-provisioner/templates/{template_dirname}")
        if os.path.exists(local_template):
            template_path = local_template
        else:
            click.echo(f"Error: Template not found at {template_path}", err=True)
            sys.exit(1)

    # Clone Repo
    remote_url = get_remote_url(
        git_provider,
        git_token,
        git_server,
        git_organization,
        infra_project_name,
        repo_name,
        base_url=git_base_url,
    )

    configure_git_https_auth(git_username, git_token, git_server)
    configure_git_identity()

    # Use local_dir if provided, otherwise repo_name
    clone_dir_name = local_dir if local_dir else repo_name
    repo_dir = os.path.join(work_dir, clone_dir_name)

    if os.path.exists(repo_dir):
        shutil.rmtree(repo_dir)  # Clean start

    if not os.path.exists(work_dir):
        os.makedirs(work_dir)

    clone_git_repo(remote_url, repo_dir)

    # Render Template
    overlays_dir = os.path.join(repo_dir, "overlays")
    if not os.path.exists(overlays_dir):
        os.makedirs(overlays_dir)

    render_template(template_path, overlays_dir, context, overwrite=True)

    # Commit & Push
    msg_suffix = env_name if env_name else "ci"
    commit_and_push(repo_dir, f"Add overlay for {project_name} ({msg_suffix})")
    click.echo("Successfully updated infra repo.")


def _init_impl(
    template_path,
    context,
    repo_name,
    template_type,
    git_organization,
    git_provider,
    git_server,
    git_base_url,
    git_username,
    git_token,
    output_dir,
    project_name,
):
    # Fallback logic
    if not os.path.exists(template_path):
        cwd = os.getcwd()
        template_dirname = os.path.basename(template_path)
        local_template = os.path.join(cwd, f"tools/luban-provisioner/templates/{template_dirname}")
        if os.path.exists(local_template):
            template_path = local_template
        else:
            click.echo(f"Error: Template not found at {template_path}", err=True)
            sys.exit(1)

    # Get Provider
    provider = get_git_provider(
        git_provider,
        git_token,
        server=git_server,
        organization=git_organization,
        project=project_name,
        base_url=git_base_url,
    )
    if not provider:
        click.echo("Error: Failed to initialize Git provider.", err=True)
        sys.exit(1)

    # Ensure Project Exists (Relevant for Azure)
    provider.create_project(project_name)

    # Create Repo if needed
    if not provider.repo_exists(repo_name):
        click.echo(f"Creating repo {repo_name}...")
        repo = provider.create_repo(
            repo_name, description=f"Luban {template_type.upper()} Infrastructure"
        )
        if not repo:
            click.echo(f"Failed to create repo {repo_name}", err=True)
            sys.exit(1)
    else:
        click.echo(f"Repo {repo_name} already exists. Updating base...")

    # Clone Repo
    remote_url = get_remote_url(
        git_provider,
        git_token,
        git_server,
        git_organization,
        project_name,
        repo_name,
        base_url=git_base_url,
    )
    repo_dir = os.path.join(output_dir, repo_name)

    configure_git_https_auth(git_username, git_token, git_server)
    configure_git_identity()

    if os.path.exists(repo_dir):
        shutil.rmtree(repo_dir)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        clone_git_repo(remote_url, repo_dir)
    except Exception as e:
        click.echo(f"Clone failed (likely empty repo): {e}. Initializing fresh...", err=True)
        os.makedirs(repo_dir, exist_ok=True)
        initialize_git_repo(repo_dir, remote_url)

    # Render Template
    # We pass repo_name in context so the template can create the directory
    if "repo_name" not in context:
        context["repo_name"] = repo_name

    render_template(template_path, output_dir, context, overwrite=True)

    # Commit & Push
    commit_and_push(repo_dir, f"Initialize {template_type.upper()} infrastructure base")
    click.echo(f"Successfully initialized {repo_name}.")


# --- CI Commands ---


@ci.command(name="update")
@click.option("--repo-name", required=True)
@click.option("--project-name", required=True, help="User Project Name")
@click.option("--git-organization", default="metasync")
@click.option("--git-provider", default="github")
@click.option("--git-server", envvar="GIT_SERVER")
@click.option(
    "--git-base-url",
    envvar="GIT_BASE_URL",
    default="",
    help="Git base URL (optional, supports path prefixes)",
)
@click.option("--git-username", envvar="GIT_USERNAME", default="git")
@click.option("--git-token", envvar="GIT_TOKEN")
@click.option("--work-dir", default="/workdir")
@click.option("--infra-project-name", default="luban-infra")
@click.option("--admin-group", required=True, help="AD Group for Admins")
@click.option("--developer-group", required=True, help="AD Group for Developers")
@click.option(
    "--image-pull-secret",
    default="harbor-creds",
    envvar="IMAGE_PULL_SECRET",
    help="Image Pull Secret Name (env: IMAGE_PULL_SECRET)",
)
@click.option("--local-dir", default=None, help="Local directory name (defaults to repo-name)")
def update_ci(
    repo_name,
    project_name,
    git_organization,
    git_provider,
    git_server,
    git_base_url,
    git_username,
    git_token,
    work_dir,
    infra_project_name,
    admin_group,
    developer_group,
    image_pull_secret,
    local_dir,
):
    """Update CI infra repo with new overlay."""
    context = {
        "project_name": project_name,
        "admin_group": admin_group,
        "developer_group": developer_group,
        "image_pull_secret": image_pull_secret,
        "git_organization": git_organization,
        "git_provider": git_provider,
    }
    _update_impl(
        "/app/templates/infra-ci-overlay",
        context,
        repo_name,
        project_name,
        None,
        git_organization,
        git_provider,
        git_server,
        git_base_url,
        git_username,
        git_token,
        work_dir,
        infra_project_name,
        local_dir=local_dir,
    )


@ci.command(name="init")
@click.option("--repo-name", required=True)
@click.option("--git-organization", default="metasync")
@click.option("--git-provider", default="github")
@click.option("--git-server", envvar="GIT_SERVER")
@click.option(
    "--git-base-url",
    envvar="GIT_BASE_URL",
    default="",
    help="Git base URL (optional, supports path prefixes)",
)
@click.option("--git-username", envvar="GIT_USERNAME", default="git")
@click.option("--git-token", envvar="GIT_TOKEN")
@click.option("--output-dir", default="/workdir")
@click.option("--project-name", default="luban-infra")
@click.option(
    "--image-pull-secret",
    default="harbor-creds",
    envvar="IMAGE_PULL_SECRET",
    help="Image Pull Secret Name (env: IMAGE_PULL_SECRET)",
)
@click.option(
    "--azure-ssh-host",
    envvar="AZURE_SSH_HOST",
    default="",
    help="Host for Azure Repos SSH (kpack.io/git annotation)",
)
@click.option(
    "--ado-ssh-host",
    envvar="ADO_SSH_HOST",
    default="",
    help="Host for ADO Server SSH (kpack.io/git annotation)",
)
def init_ci(
    repo_name,
    git_organization,
    git_provider,
    git_server,
    git_base_url,
    git_username,
    git_token,
    output_dir,
    project_name,
    image_pull_secret,
    azure_ssh_host,
    ado_ssh_host,
):
    """Initialize CI infra repo with base structure."""

    def _normalize_host(host):
        if not host:
            return ""
        host = host.strip()
        host = host.removeprefix("https://").removeprefix("http://")
        host = host.split("/", 1)[0]
        host = host.split(":", 1)[0]
        return host

    if not azure_ssh_host and git_provider == "azure":
        if git_server and git_server not in ("dev.azure.com", "ssh.dev.azure.com"):
            azure_ssh_host = git_server
        else:
            azure_ssh_host = "ssh.dev.azure.com"

    if not ado_ssh_host and git_provider == "ado":
        ado_ssh_host = git_base_url or git_server

    azure_ssh_host = _normalize_host(azure_ssh_host)
    ado_ssh_host = _normalize_host(ado_ssh_host)

    context = {
        "image_pull_secret": image_pull_secret,
        "azure_ssh_host": azure_ssh_host,
        "ado_ssh_host": ado_ssh_host,
    }
    _init_impl(
        "/app/templates/infra-ci-base",
        context,
        repo_name,
        "ci",
        git_organization,
        git_provider,
        git_server,
        git_base_url,
        git_username,
        git_token,
        output_dir,
        project_name,
    )


# --- CD Commands ---


@cd.command(name="update")
@click.option("--repo-name", required=True)
@click.option("--project-name", required=True, help="User Project Name")
@click.option("--env", required=True, help="Environment (snd/prd)")
@click.option("--git-organization", default="metasync")
@click.option("--git-provider", default="github")
@click.option("--git-server", envvar="GIT_SERVER")
@click.option(
    "--git-base-url",
    envvar="GIT_BASE_URL",
    default="",
    help="Git base URL (optional, supports path prefixes)",
)
@click.option("--git-username", envvar="GIT_USERNAME", default="git")
@click.option("--git-token", envvar="GIT_TOKEN")
@click.option("--work-dir", default="/workdir")
@click.option("--infra-project-name", default="luban-infra")
@click.option(
    "--image-pull-secret",
    default="harbor-creds",
    envvar="IMAGE_PULL_SECRET",
    help="Image Pull Secret Name (env: IMAGE_PULL_SECRET)",
)
@click.option("--local-dir", default=None, help="Local directory name (defaults to repo-name)")
def update_cd(
    repo_name,
    project_name,
    env,
    git_organization,
    git_provider,
    git_server,
    git_base_url,
    git_username,
    git_token,
    work_dir,
    infra_project_name,
    image_pull_secret,
    local_dir,
):
    """Update CD infra repo with new overlay."""
    context = {
        "project_name": project_name,
        "env": env,
        "image_pull_secret": image_pull_secret,
        "git_organization": git_organization,
        "git_provider": git_provider,
    }
    _update_impl(
        "/app/templates/infra-cd-overlay",
        context,
        repo_name,
        project_name,
        env,
        git_organization,
        git_provider,
        git_server,
        git_base_url,
        git_username,
        git_token,
        work_dir,
        infra_project_name,
        local_dir=local_dir,
    )


@cd.command(name="init")
@click.option("--repo-name", required=True)
@click.option("--git-organization", default="metasync")
@click.option("--git-provider", default="github")
@click.option("--git-server", envvar="GIT_SERVER")
@click.option(
    "--git-base-url",
    envvar="GIT_BASE_URL",
    default="",
    help="Git base URL (optional, supports path prefixes)",
)
@click.option("--git-username", envvar="GIT_USERNAME", default="git")
@click.option("--git-token", envvar="GIT_TOKEN")
@click.option("--output-dir", default="/workdir")
@click.option("--project-name", default="luban-infra")
@click.option(
    "--image-pull-secret",
    default="harbor-creds",
    envvar="IMAGE_PULL_SECRET",
    help="Image Pull Secret Name (env: IMAGE_PULL_SECRET)",
)
def init_cd(
    repo_name,
    git_organization,
    git_provider,
    git_server,
    git_base_url,
    git_username,
    git_token,
    output_dir,
    project_name,
    image_pull_secret,
):
    """Initialize CD infra repo with base structure."""
    context = {"image_pull_secret": image_pull_secret}
    _init_impl(
        "/app/templates/infra-cd-base",
        context,
        repo_name,
        "cd",
        git_organization,
        git_provider,
        git_server,
        git_base_url,
        git_username,
        git_token,
        output_dir,
        project_name,
    )
