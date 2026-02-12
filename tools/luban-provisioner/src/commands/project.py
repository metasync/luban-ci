import os
import sys
import click
from provider_factory import get_git_provider

@click.command(name='project')
@click.option('--project-name', required=True, help='Name of the project')
@click.option('--git-org', required=True, help='Git Organization')
@click.option('--git-provider', default='github', help='Git Provider')
@click.option('--git-token', envvar='GIT_TOKEN', required=True, help='Git Token (env: GIT_TOKEN)')
@click.option('--git-server', envvar='GIT_SERVER', required=True, help='Git Server Domain (env: GIT_SERVER)')
def project(project_name, git_org, git_provider, git_token, git_server):
    """Ensure Git Project/Organization exists."""

    provider = get_git_provider(git_provider, git_token, server=git_server, organization=git_org, project=project_name)

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
