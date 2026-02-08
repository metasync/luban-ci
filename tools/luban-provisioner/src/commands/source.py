import sys
import os
import click
from cookiecutter.main import cookiecutter
from providers.github import GitHubProvider
from utils import initialize_git_repo

@click.command(name='source')
@click.option('--project-name', required=True, help='Name of the project (e.g., team name)')
@click.option('--application-name', required=True, help='Name of the application')
@click.option('--output-dir', required=True, help='Directory to output the rendered template')
@click.option('--git-organization', default='metasync', help='Git Organization')
@click.option('--git-provider', default='github', help='Git Provider')
@click.option('--webhook-url', required=False, help='Webhook URL')
@click.option('--github-token', envvar='GITHUB_TOKEN', help='GitHub Token')
@click.option('--webhook-secret', envvar='WEBHOOK_SECRET', help='Webhook Secret')
def source(project_name, application_name, output_dir, git_organization, git_provider, webhook_url, github_token, webhook_secret):
    """Provision Source Code Repository"""
    
    # Git Provider Logic - Pre-check
    org = git_organization if git_organization else project_name
    repo_name = application_name

    if git_provider == 'github':
        if not github_token:
            click.echo("GITHUB_TOKEN not provided", err=True)
            sys.exit(1)
        
        provider = GitHubProvider(github_token)
        
        if provider.repo_exists(org, repo_name):
            click.echo(f"Repository {org}/{repo_name} already exists. Skipping.")
            sys.exit(0)

    template_path = "/app/templates/source/luban-python-template"
    
    package_name = application_name.replace('-', '_')
    extra_context = {
        "project_name": project_name, 
        "app_name": application_name,
        "package_name": package_name,
        "description": "A sample Python app for Luban CI. Replace this with your own description.",
        "version": "0.1.0"
    }

    click.echo(f"Provisioning source repo for app {application_name} in project {project_name}...")
    click.echo(f"Context: {extra_context}")
    
    try:
        cookiecutter(
            template_path,
            no_input=True,
            output_dir=output_dir,
            extra_context=extra_context
        )
        click.echo(f"Successfully generated template in {output_dir}/{application_name}")
    except Exception as e:
        click.echo(f"Error generating template: {e}", err=True)
        sys.exit(1)

    # Post-provisioning: Push to Git
    if git_provider == 'github':
        # Create Repo
        repo = provider.create_repo(repo_name, org=org, description=extra_context["description"])
        if not repo:
            click.echo("Failed to create repository", err=True)
            sys.exit(1)
            
        # Configure Webhook
        if webhook_url and webhook_secret:
            provider.create_webhook(org, repo_name, webhook_url, webhook_secret)
            
        # Push
        repo_dir = os.path.join(output_dir, application_name)
        remote_url = f"https://{github_token}@github.com/{org}/{repo_name}.git"
        initialize_git_repo(repo_dir, remote_url)
