import sys
import os
import click
from cookiecutter.main import cookiecutter
from providers.github import GitHubProvider
from providers.azure import AzureProvider
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
@click.option('--azure-token', envvar='AZURE_DEVOPS_TOKEN', help='Azure DevOps Token')
@click.option('--git-server', default=None, help='Git Server Domain (e.g., github.com, dev.azure.com)')
def gitops(project_name, application_name, output_dir, container_port, service_port, domain_suffix, default_image_name, default_image_tag, git_organization, git_provider, github_token, azure_token, git_server):
    """Provision GitOps Repository"""
    
    # Git Provider Logic - Pre-check
    org = git_organization if git_organization else project_name
    repo_name = f"{application_name}-gitops"
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
            
            # Azure DevOps uses Organization and Project hierarchy.
            # We assume git_organization is the ADO Organization and project_name is the ADO Project.
            click.echo(f"Connecting to Azure DevOps Organization: '{org}', Project: '{project_name}'")
            provider = AzureProvider(azure_token, organization=org, project=project_name, git_server=git_server)
            
            if provider.repo_exists(repo_name):
                click.echo(f"Repository {repo_name} already exists in project {project_name}. Skipping.")
                sys.exit(0)
        
        case _:
            click.echo(f"Unsupported git provider: {git_provider}", err=True)
            sys.exit(1)

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
    if provider:
        # Create Repo
        repo = provider.create_repo(repo_name, description=f"GitOps configuration for {application_name}")
        if not repo:
            click.echo("Failed to create repository", err=True)
            sys.exit(1)
            
        # Init and Push Main
        repo_dir = os.path.join(output_dir, repo_name)
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
        
        # Create Develop and Push
        create_and_push_branch(repo_dir, "develop")
        
        # Configure Settings
        if git_provider == 'github':
            provider.set_default_branch(org, repo_name, "develop")
            provider.enable_branch_protection(org, repo_name, "main")
        elif git_provider == 'azure':
            provider.set_default_branch(repo.get('id'), "develop")
            provider.enable_branch_protection(repo.get('id'), "main")
