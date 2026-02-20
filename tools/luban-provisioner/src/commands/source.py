import sys
import os
import click
from utils import initialize_git_repo, render_template, load_config
from provider_factory import get_git_provider, get_remote_url

@click.command(name='source')
@click.option('--project-name', required=True, help='Name of the project (e.g., team name)')
@click.option('--application-name', required=True, help='Name of the application')
@click.option('--output-dir', required=True, help='Directory to output the rendered template')
@click.option('--git-organization', default='metasync', help='Git Organization')
@click.option('--git-provider', default='github', help='Git Provider')
@click.option('--webhook-url', required=False, help='Webhook URL')
@click.option('--git-token', envvar='GIT_TOKEN', required=True, help='Git Token (env: GIT_TOKEN)')
@click.option('--webhook-secret', envvar='WEBHOOK_SECRET', help='Webhook Secret')
@click.option('--git-server', envvar='GIT_SERVER', required=True, help='Git Server Domain (env: GIT_SERVER)')
@click.option('--template-type', default='python', help='Template type: python, dagster-code-location')
@click.option('--config-file', required=False, help='Path to configuration file (YAML/JSON)')
@click.option('--set', multiple=True, help='Set extra context values (key=value)')
def source(project_name, application_name, output_dir, git_organization, git_provider, webhook_url, git_token, webhook_secret, git_server, template_type, config_file, set):
    """Provision Source Code Repository"""
    
    # Load config file
    config = load_config(config_file)
    
    # Parse set options
    cli_extra_context = {}
    for item in set:
        if '=' in item:
            key, value = item.split('=', 1)
            cli_extra_context[key] = value
        else:
            click.echo(f"Warning: Invalid set option '{item}'. Must be key=value", err=True)

    template_type = template_type if template_type != 'python' else config.get('template_type', 'python')
    
    # Git Provider Logic - Pre-check
    org = git_organization if git_organization else project_name
    repo_name = application_name
    
    provider = get_git_provider(git_provider, git_token, server=git_server, organization=org, project=project_name)
    
    if provider.repo_exists(repo_name):
        click.echo(f"Repository {repo_name} already exists. Skipping.")
        sys.exit(0)

    # Template Selection
    match template_type:
        case 'dagster-platform':
            template_path = "/app/templates/source/luban-dagster-platform-source-template"
            description = f"Dagster Platform for {application_name}"
        case 'dagster-code-location':
            template_path = "/app/templates/source/luban-dagster-code-location-source-template"
            description = f"Dagster Code Location for {application_name}"
        case 'python':
            template_path = "/app/templates/source/luban-python-template"
            description = f"A sample Python app for {application_name}. Replace this with your own description."
        case _:
            click.echo(f"Unknown template type: {template_type}", err=True)
            sys.exit(1)
    
    package_name = application_name.replace('-', '_')
    
    extra_context = {
        "project_name": project_name, 
        "app_name": application_name,
        "package_name": package_name,
        "author_name": "Data Team", # Default
        "author_email": "data@luban-ci.io", # Default
        "description": description,
        "version": "0.1.0"
    }
    
    # Merge config into extra_context
    for k, v in config.items():
        if k not in extra_context:
            extra_context[k] = v

    # Merge CLI extra context (takes precedence)
    extra_context.update(cli_extra_context)
    
    if "image_tag" not in extra_context:
        extra_context["image_tag"] = "latest"

    # Fallback logic for webhook_url
    if not webhook_url:
        webhook_url = config.get('webhook_url')

    click.echo(f"Provisioning source repo for app {application_name} in project {project_name}...")
    click.echo(f"Context: {extra_context}")
    
    try:
        render_template(template_path, output_dir, extra_context)
    except Exception as e:
        sys.exit(1)

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
        remote_url = get_remote_url(git_provider, git_token, git_server, org, project_name, repo_name)
            
        initialize_git_repo(repo_dir, remote_url)
