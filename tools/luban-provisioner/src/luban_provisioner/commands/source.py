import os
import sys

import click

from luban_provisioner.cli.common import format_context_for_log, parse_set_overrides
from luban_provisioner.config.io import load_config
from luban_provisioner.git.repo import initialize_git_repo
from luban_provisioner.git.setup import prepare_git_https
from luban_provisioner.provider_factory import get_git_provider, get_remote_url
from luban_provisioner.templates.paths import resolve_template_path
from luban_provisioner.templates.render import render_template


@click.command(name="source")
@click.option("--project-name", required=True, help="Name of the project (e.g., team name)")
@click.option("--application-name", required=True, help="Name of the application")
@click.option("--output-dir", required=True, help="Directory to output the rendered template")
@click.option("--git-organization", default="metasync", help="Git Organization")
@click.option("--git-provider", default="github", help="Git Provider")
@click.option("--webhook-url", required=False, help="Webhook URL")
@click.option(
    "--git-username", envvar="GIT_USERNAME", default="git", help="Git Username (env: GIT_USERNAME)"
)
@click.option("--git-token", envvar="GIT_TOKEN", required=True, help="Git Token (env: GIT_TOKEN)")
@click.option("--webhook-secret", envvar="WEBHOOK_SECRET", help="Webhook Secret")
@click.option(
    "--git-server", envvar="GIT_SERVER", required=True, help="Git Server Domain (env: GIT_SERVER)"
)
@click.option(
    "--template-type",
    default="python",
    help="Template type: python, dagster-platform, dagster-code-location, dagster-dbt-starrocks-code-location",
)
@click.option("--config-file", required=False, help="Path to configuration file (YAML/JSON)")
@click.option("--set", multiple=True, help="Set extra context values (key=value)")
@click.option("--dry-run/--no-dry-run", default=False, help="Render only; skip provider operations")
def source(
    project_name,
    application_name,
    output_dir,
    git_organization,
    git_provider,
    webhook_url,
    git_username,
    git_token,
    webhook_secret,
    git_server,
    template_type,
    config_file,
    set,
    dry_run,
):
    """Provision Source Code Repository"""

    # Load config file
    config = load_config(config_file)

    # Parse set options
    cli_extra_context = parse_set_overrides(set)

    template_type = (
        template_type if template_type != "python" else config.get("template_type", "python")
    )

    # Git Provider Logic - Pre-check
    org = git_organization if git_organization else project_name
    repo_name = application_name

    git_base_url = None
    provider = None
    if not dry_run:
        from luban_provisioner.git.auth import apply_git_https_config

        git_base_url = apply_git_https_config(config, git_provider, git_server)
        provider = get_git_provider(
            git_provider,
            git_token,
            server=git_server,
            organization=org,
            project=project_name,
            base_url=git_base_url,
        )

        if provider.repo_exists(repo_name):
            click.echo(f"Repository {repo_name} already exists. Skipping.")
            sys.exit(0)

    package_name = application_name.replace("-", "_")

    match template_type:
        case "dagster-platform":
            template_path = "/app/templates/source/luban-dagster-platform-source-template"
            description = f"Dagster Platform for {application_name}"
        case "dagster-code-location":
            template_path = "/app/templates/source/luban-dagster-code-location-source-template"
            description = f"Dagster Code Location for {application_name}"
        case "dagster-dbt-starrocks-code-location":
            template_path = (
                "/app/templates/source/luban-dagster-dbt-starrocks-code-location-source-template"
            )
            description = f"Dagster + dbt (StarRocks) Code Location for {application_name}"
        case "python":
            template_path = "/app/templates/source/luban-python-template"
            description = f"A sample Python app for {application_name}. Replace this with your own description."
        case _:
            click.echo(f"Unknown template type: {template_type}", err=True)
            sys.exit(1)

    try:
        template_path = resolve_template_path(template_path)
    except FileNotFoundError:
        sys.exit(1)

    extra_context = {
        "project_name": project_name,
        "app_name": application_name,
        "package_name": package_name,
        "author_name": "Data Team",
        "author_email": "data@luban-ci.io",
        "description": description,
        "version": "0.1.0",
    }

    for k, v in (config or {}).items():
        if k not in extra_context:
            extra_context[k] = v

    extra_context.update(cli_extra_context)

    if template_type == "dagster-dbt-starrocks-code-location":
        extra_context.setdefault("dagster_version", "1.12.19")
        extra_context.setdefault("default_env", "development")
        extra_context.setdefault("code_location_port", "3000")

    if "image_tag" not in extra_context:
        extra_context["image_tag"] = "latest"

    # Fallback logic for webhook_url
    if not webhook_url:
        webhook_url = config.get("webhook_url")

    click.echo(f"Provisioning source repo for app {application_name} in project {project_name}...")
    formatted_context = format_context_for_log(extra_context)
    if formatted_context is not None:
        click.echo(f"Context: {formatted_context}")

    try:
        render_template(template_path, output_dir, extra_context)
    except Exception:
        sys.exit(1)

    if dry_run:
        click.echo("Dry run: skipping provider operations.")
        return

    # Post-provisioning: Push to Git
    if provider:
        # Create Repo
        repo = provider.create_repo(repo_name, description=extra_context["description"])
        if not repo:
            click.echo("Failed to create repository", err=True)
            sys.exit(1)

        # Configure Webhook
        if webhook_url:
            provider.create_webhook(repo, webhook_url, secret=webhook_secret)

        # Push
        repo_dir = os.path.join(output_dir, application_name)
        remote_url = get_remote_url(
            git_provider, git_token, git_server, org, project_name, repo_name, base_url=git_base_url
        )

        prepare_git_https(git_username, git_token, git_server)

        initialize_git_repo(repo_dir, remote_url)
