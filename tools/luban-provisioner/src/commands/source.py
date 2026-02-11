import sys
import os
import click
from cookiecutter.main import cookiecutter
from providers.github import GitHubProvider
from providers.azure import AzureProvider
from utils import initialize_git_repo

@click.command(name='source')
@click.option('--project-name', required=True, help='Name of the project (e.g., team name)')
@click.option('--application-name', required=True, help='Name of the application')
@click.option('--output-dir', required=True, help='Directory to output the rendered template')
@click.option('--git-organization', default='metasync', help='Git Organization')
@click.option('--git-provider', default='github', help='Git Provider')
@click.option('--webhook-url', required=False, help='Webhook URL')
@click.option('--github-token', envvar='GITHUB_TOKEN', help='GitHub Token')
@click.option('--azure-token', envvar='AZURE_DEVOPS_TOKEN', help='Azure DevOps Token')
@click.option('--webhook-secret', envvar='WEBHOOK_SECRET', help='Webhook Secret')
@click.option('--git-server', default=None, help='Git Server Domain (e.g., github.com, dev.azure.com)')
def source(project_name, application_name, output_dir, git_organization, git_provider, webhook_url, github_token, azure_token, webhook_secret, git_server):
    """Provision Source Code Repository"""
    
    # Git Provider Logic - Pre-check
    org = git_organization if git_organization else project_name
    repo_name = application_name
    provider = None

    # Resolve defaults if git_server not provided
    if not git_server:
        if git_provider == 'github':
            git_server = 'github.com'
        elif git_provider == 'azure':
            git_server = 'dev.azure.com'

    match git_provider:
        case 'github':
            if not github_token:
                click.echo("GITHUB_TOKEN not provided", err=True)
                sys.exit(1)
            
            provider = GitHubProvider(github_token, git_server=git_server)
            
            if provider.repo_exists(org, repo_name):
                click.echo(f"Repository {org}/{repo_name} already exists. Skipping.")
                sys.exit(0)
        
        case 'azure':
            if not azure_token:
                click.echo("AZURE_DEVOPS_TOKEN not provided", err=True)
                sys.exit(1)
            
            provider = AzureProvider(azure_token, organization=org, project=project_name, git_server=git_server)
            
            if provider.repo_exists(repo_name):
                click.echo(f"Repository {repo_name} already exists in project {project_name}. Skipping.")
                sys.exit(0)

        case _:
            click.echo(f"Unsupported git provider: {git_provider}", err=True)
            sys.exit(1)

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
    if provider:
        # Create Repo
        repo = provider.create_repo(repo_name, description=extra_context["description"])
        if not repo:
            click.echo("Failed to create repository", err=True)
            sys.exit(1)
            
        # Configure Webhook
        if webhook_url:
            match git_provider:
                case 'github':
                    if webhook_secret:
                        provider.create_webhook(org, repo_name, webhook_url, webhook_secret)
                case 'azure':
                    # Pass webhook_secret to Azure provider as well
                    provider.create_webhook(repo.get('id'), webhook_url, secret=webhook_secret)
            
        # Push
        repo_dir = os.path.join(output_dir, application_name)
        remote_url = ""

        match git_provider:
            case 'github':
                remote_url = f"https://{github_token}@{git_server}/{org}/{repo_name}.git"
            case 'azure':
                # Use HTTPS with embedded credentials for provisioning
                # Format: https://{token}@{git_server}/{org}/{project}/_git/{repo}
                # Azure DevOps allows arbitrary username with PAT as password.
                remote_url = f"https://git:{azure_token}@{git_server}/{org}/{project_name}/_git/{repo_name}"
            
        initialize_git_repo(repo_dir, remote_url)
