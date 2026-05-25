import os
import sys

import click

from luban_provisioner.commands.gitops import gitops
from luban_provisioner.commands.infra import init_cd, init_ci, update_cd, update_ci
from luban_provisioner.commands.source import source


@click.command(name="dry-run")
@click.option("--output-dir", default="/tmp/luban-provisioner-dry-run", show_default=True)
@click.option("--project-name", required=True)
@click.option("--application-name", required=True)
@click.option("--git-provider", default="github")
@click.option("--git-server", required=True)
@click.option("--git-token", required=True)
@click.option("--git-organization", default="metasync")
@click.option("--domain-suffix", default="example.com", show_default=True)
@click.option("--container-port", default="8080", show_default=True)
@click.option("--service-port", default="80", show_default=True)
@click.option("--infra-ci-repo", default="luban-infra-ci", show_default=True)
@click.option("--infra-cd-repo", default="luban-infra-cd", show_default=True)
@click.option("--admin-group", default="demo-admin", show_default=True)
@click.option("--developer-group", default="demo-dev", show_default=True)
@click.option("--image-pull-secret", default="harbor-creds", show_default=True)
@click.option("--env", default="snd", show_default=True)
def dry_run(
    output_dir,
    project_name,
    application_name,
    git_provider,
    git_server,
    git_token,
    git_organization,
    domain_suffix,
    container_port,
    service_port,
    infra_ci_repo,
    infra_cd_repo,
    admin_group,
    developer_group,
    image_pull_secret,
    env,
):
    """Render source/gitops/infra templates locally without provider/git operations."""

    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    ctx = click.get_current_context()

    click.echo(f"Dry run output: {output_dir}")

    click.echo("Rendering source template...")
    rc = ctx.invoke(
        source,
        dry_run=True,
        project_name=project_name,
        application_name=application_name,
        output_dir=output_dir,
        git_organization=git_organization,
        git_provider=git_provider,
        webhook_url=None,
        git_username="git",
        git_token=git_token,
        webhook_secret=None,
        git_server=git_server,
        template_type="python",
        config_file=None,
        set=(),
    )
    if rc is not None:
        sys.exit(1)

    click.echo("Rendering gitops template...")
    rc = ctx.invoke(
        gitops,
        dry_run=True,
        project_name=project_name,
        application_name=application_name,
        output_dir=output_dir,
        container_port=str(container_port),
        service_port=str(service_port),
        domain_suffix=domain_suffix,
        default_image_name=None,
        default_image_tag=None,
        git_organization=git_organization,
        git_provider=git_provider,
        git_username="git",
        git_token=git_token,
        git_server=git_server,
        template_type="standard",
        config_file=None,
        set=(),
    )
    if rc is not None:
        sys.exit(1)

    click.echo("Rendering infra templates...")
    ctx.invoke(
        init_ci,
        dry_run=True,
        dry_run_dir=os.path.join(output_dir, "infra-ci-base"),
        repo_name=infra_ci_repo,
        git_organization=git_organization,
        git_provider=git_provider,
        git_server=git_server,
        git_base_url="",
        git_username="git",
        git_token=git_token,
        output_dir="/tmp/unused",
        project_name="luban-infra",
        image_pull_secret=image_pull_secret,
        azure_ssh_host="",
        ado_ssh_host="",
    )
    ctx.invoke(
        update_ci,
        dry_run=True,
        dry_run_dir=os.path.join(output_dir, "infra-ci-overlay"),
        repo_name=infra_ci_repo,
        project_name=project_name,
        git_organization=git_organization,
        git_provider=git_provider,
        git_server=git_server,
        git_base_url="",
        git_username="git",
        git_token=git_token,
        work_dir="/tmp/unused",
        infra_project_name="luban-infra",
        admin_group=admin_group,
        developer_group=developer_group,
        image_pull_secret=image_pull_secret,
        local_dir=None,
    )
    ctx.invoke(
        init_cd,
        dry_run=True,
        dry_run_dir=os.path.join(output_dir, "infra-cd-base"),
        repo_name=infra_cd_repo,
        git_organization=git_organization,
        git_provider=git_provider,
        git_server=git_server,
        git_base_url="",
        git_username="git",
        git_token=git_token,
        output_dir="/tmp/unused",
        project_name="luban-infra",
        image_pull_secret=image_pull_secret,
    )
    ctx.invoke(
        update_cd,
        dry_run=True,
        dry_run_dir=os.path.join(output_dir, "infra-cd-overlay"),
        repo_name=infra_cd_repo,
        project_name=project_name,
        env=env,
        git_organization=git_organization,
        git_provider=git_provider,
        git_server=git_server,
        git_base_url="",
        git_username="git",
        git_token=git_token,
        work_dir="/tmp/unused",
        infra_project_name="luban-infra",
        image_pull_secret=image_pull_secret,
        local_dir=None,
    )

    click.echo("Dry run complete.")
