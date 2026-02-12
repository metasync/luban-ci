import sys
import os
import click
from utils import initialize_git_repo, create_and_push_branch, render_template
from provider_factory import get_git_provider, get_remote_url

@click.command(name='gitops')
@click.option('--project-name', required=True, help='Name of the project/repo')
@click.option('--application-name', required=True, help='Name of the application')
@click.option('--output-dir', required=True, help='Directory to output the rendered template')
@click.option('--container-port', required=True, help='Port exposed by the container')
@click.option('--service-port', required=True, help='Port exposed by the service')
@click.option('--domain-suffix', required=True, help='Domain suffix for ingress/routes')
@click.option('--default-image-name', required=False, help='Default image name')
@click.option('--default-image-tag', required=False, help='Default image tag')
@click.option('--git-organization', default='metasync', help='Git Organization')
@click.option('--git-provider', default='github', help='Git Provider')
@click.option('--git-token', envvar='GIT_TOKEN', required=True, help='Git Token (env: GIT_TOKEN)')
@click.option('--git-server', envvar='GIT_SERVER', required=True, help='Git Server Domain (env: GIT_SERVER)')
def gitops(project_name, application_name, output_dir, container_port, service_port, domain_suffix, default_image_name, default_image_tag, git_organization, git_provider, git_token, git_server):
    """Provision GitOps Repository"""
    
    # Git Provider Logic - Pre-check
    org = git_organization if git_organization else project_name
    repo_name = f"{application_name}-gitops"
    
    provider = get_git_provider(git_provider, git_token, server=git_server, organization=org, project=project_name)
    
    if provider.repo_exists(repo_name):
        click.echo(f"Repository {repo_name} already exists. Skipping.")
        sys.exit(0)

    template_path = "/app/templates/gitops/luban-gitops-template"
    
    extra_context = {
        "project_name": project_name,
        "app_name": application_name,
        "container_port": container_port,
        "service_port": service_port,
        "domain_suffix": domain_suffix
    }
    
    if default_image_name:
        extra_context["default_image_name"] = default_image_name
    if default_image_tag:
        extra_context["default_image_tag"] = default_image_tag

    click.echo(f"Provisioning GitOps repo for app {application_name} in project {project_name}...")
    click.echo(f"Context: {extra_context}")
    
    try:
        render_template(template_path, output_dir, extra_context)
    except Exception as e:
        sys.exit(1)

    # Post-provisioning: Push to Git
    if provider:
        # Create Repo
        repo = provider.create_repo(repo_name, description=f"GitOps configuration for {application_name}")
        if not repo:
            click.echo("Failed to create repository", err=True)
            sys.exit(1)
            
        # Init and Push Main
        repo_dir = os.path.join(output_dir, repo_name)
        remote_url = get_remote_url(git_provider, git_token, git_server, org, project_name, repo_name)

        initialize_git_repo(repo_dir, remote_url)
        
        # Create Develop and Push
        create_and_push_branch(repo_dir, "develop")
        
        # Configure Settings
        provider.set_default_branch(repo, "develop")
        provider.enable_branch_protection(repo, "main")
