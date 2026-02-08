import sys
import os
import click
from cookiecutter.main import cookiecutter
from providers.github import GitHubProvider
from utils import initialize_git_repo, create_and_push_branch

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
@click.option('--github-token', envvar='GITHUB_TOKEN', help='GitHub Token')
def gitops(project_name, application_name, output_dir, container_port, service_port, domain_suffix, default_image_name, default_image_tag, git_organization, git_provider, github_token):
    """Provision GitOps Repository"""
    
    # Git Provider Logic - Pre-check
    org = git_organization if git_organization else project_name
    repo_name = f"{application_name}-gitops"

    if git_provider == 'github':
        if not github_token:
            click.echo("GITHUB_TOKEN not provided", err=True)
            sys.exit(1)
        
        provider = GitHubProvider(github_token)
        
        if provider.repo_exists(org, repo_name):
            click.echo(f"Repository {org}/{repo_name} already exists. Skipping.")
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
        cookiecutter(
            template_path,
            no_input=True,
            output_dir=output_dir,
            extra_context=extra_context
        )
        click.echo(f"Successfully generated template in {output_dir}/{repo_name}")
    except Exception as e:
        click.echo(f"Error generating template: {e}", err=True)
        sys.exit(1)

    # Post-provisioning: Push to Git
    if git_provider == 'github':
        # Create Repo
        repo = provider.create_repo(repo_name, org=org, description=f"GitOps configuration for {application_name}")
        if not repo:
            click.echo("Failed to create repository", err=True)
            sys.exit(1)
            
        # Init and Push Main
        repo_dir = os.path.join(output_dir, repo_name)
        remote_url = f"https://{github_token}@github.com/{org}/{repo_name}.git"
        initialize_git_repo(repo_dir, remote_url)
        
        # Create Develop and Push
        create_and_push_branch(repo_dir, "develop")
        
        # Configure Settings
        provider.set_default_branch(org, repo_name, "develop")
        provider.enable_branch_protection(org, repo_name, "main")
