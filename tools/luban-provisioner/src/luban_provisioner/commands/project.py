import sys
import click
from luban_provisioner.provider_factory import get_git_provider

@click.command(name='project')
@click.option('--project-name', required=True, help='Name of the project')
@click.option('--git-organization', required=True, help='Git Organization')
@click.option('--git-provider', default='github', help='Git Provider')
@click.option('--git-token', envvar='GIT_TOKEN', required=True, help='Git Token (env: GIT_TOKEN)')
@click.option('--git-server', envvar='GIT_SERVER', required=True, help='Git Server Domain (env: GIT_SERVER)')
@click.option('--admin-group', default='', help='AD Group for Project Admins')
@click.option('--developer-group', default='', help='AD Group for Project Developers')
@click.option('--image-pull-secret', default='', envvar='IMAGE_PULL_SECRET', help='Name of the image pull secret to use (env: IMAGE_PULL_SECRET)')
def project(project_name, git_organization, git_provider, git_token, git_server, admin_group, developer_group, image_pull_secret):
    """Ensure Git Project/Organization exists."""

    provider = get_git_provider(git_provider, git_token, server=git_server, organization=git_organization, project=project_name)

    if provider:
        try:
            # We pass description based on context
            desc = f"Project {project_name} created by Luban Provisioner"
            result = provider.create_project(project_name, description=desc)
            if not result and git_provider == 'azure':
                click.echo("Failed to create/verify Azure project. Aborting.", err=True)
                sys.exit(1)
        except Exception as e:
            click.echo(f"Error creating/verifying git project: {e}", err=True)
            # If Git Project creation fails, subsequent repo creation will fail.
            # Fail hard for Azure as it's critical.
            if git_provider == 'azure':
                sys.exit(1)
