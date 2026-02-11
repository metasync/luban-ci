import os
import sys
import click
from providers.github import GitHubProvider
from providers.azure import AzureProvider

@click.command(name='project')
@click.option('--project-name', required=True, help='Name of the project')
@click.option('--git-org', required=True, help='Git Organization')
@click.option('--git-provider', default='github', help='Git Provider')
@click.option('--github-token', envvar='GITHUB_TOKEN', help='GitHub Token')
@click.option('--azure-token', envvar='AZURE_DEVOPS_TOKEN', help='Azure DevOps Token')
@click.option('--git-server', default=None, help='Git Server Domain (e.g., github.com, dev.azure.com)')
def project(project_name, git_org, git_provider, github_token, azure_token, git_server):
    """Ensure Git Project/Organization exists."""

    # Resolve defaults if git_server not provided
    if not git_server:
        if git_provider == 'github':
            git_server = 'github.com'
        elif git_provider == 'azure':
            git_server = 'dev.azure.com'

    provider = None
    match git_provider:
        case 'github':
            if not github_token:
                click.echo("Warning: GITHUB_TOKEN not provided. Skipping Git project verification/creation.", err=True)
            else:
                provider = GitHubProvider(github_token, git_server=git_server)
        
        case 'azure':
            if not azure_token:
                click.echo("Warning: AZURE_DEVOPS_TOKEN not provided. Skipping Azure project creation.", err=True)
            else:
                # For Azure, project_name is the Project Name. git_org is the Organization.
                provider = AzureProvider(azure_token, organization=git_org, project=project_name, git_server=git_server)

    if provider:
        try:
            # We pass description based on context
            desc = f"Project {project_name} created by Luban Provisioner"
            provider.create_project(project_name, description=desc)
        except Exception as e:
            click.echo(f"Error creating/verifying git project: {e}", err=True)
            # If Git Project creation fails, subsequent repo creation will fail.
            # Fail hard for Azure as it's critical.
            if git_provider == 'azure':
                sys.exit(1)
