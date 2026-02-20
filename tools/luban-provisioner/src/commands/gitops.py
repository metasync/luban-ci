import sys
import os
import click

from utils import initialize_git_repo, create_and_push_branch, render_template, load_config
from provider_factory import get_git_provider, get_remote_url

@click.command(name='gitops')
@click.option('--project-name', required=True, help='Name of the project/repo')
@click.option('--application-name', required=True, help='Name of the application')
@click.option('--output-dir', required=True, help='Directory to output the rendered template')
@click.option('--container-port', required=False, help='Port exposed by the container')
@click.option('--service-port', required=False, help='Port exposed by the service')
@click.option('--domain-suffix', required=False, help='Domain suffix for ingress/routes')
@click.option('--default-image-name', required=False, help='Default image name')
@click.option('--default-image-tag', required=False, help='Default image tag')
@click.option('--git-organization', default='metasync', help='Git Organization')
@click.option('--git-provider', default='github', help='Git Provider')
@click.option('--git-token', envvar='GIT_TOKEN', required=True, help='Git Token (env: GIT_TOKEN)')
@click.option('--git-server', envvar='GIT_SERVER', required=True, help='Git Server Domain (env: GIT_SERVER)')
@click.option('--template-type', default='standard', help='Template type: standard, dagster-platform, dagster-code-location')
@click.option('--config-file', required=False, help='Path to configuration file (YAML/JSON)')
@click.option('--set', multiple=True, help='Set extra context values (key=value)')
def gitops(project_name, application_name, output_dir, container_port, service_port, domain_suffix, default_image_name, default_image_tag, git_organization, git_provider, git_token, git_server, template_type, config_file, set):
    """Provision GitOps Repository"""
    
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
    
    # Merge config with CLI args (CLI args take precedence if provided, otherwise fallback to config)
    # Note: For optional args, we check if they are None from CLI
    
    container_port = container_port or config.get('container_port')
    service_port = service_port or config.get('service_port')
    domain_suffix = domain_suffix or config.get('domain_suffix')
    default_image_name = default_image_name or config.get('default_image_name')
    default_image_tag = default_image_tag or config.get('default_image_tag')
    template_type = template_type if template_type != 'standard' else config.get('template_type', 'standard')
    
    # Validate required fields (since CLI args are now optional)
    is_dagster = template_type.startswith('dagster')
    is_dagster_code_location = template_type == 'dagster-code-location'
    
    if not container_port and not is_dagster:
        click.echo("Error: --container-port is required (or must be in config file) for standard templates", err=True)
        sys.exit(1)
    if not service_port and not is_dagster:
        click.echo("Error: --service-port is required (or must be in config file) for standard templates", err=True)
        sys.exit(1)
    if not domain_suffix and not is_dagster_code_location:
        click.echo("Error: --domain-suffix is required (or must be in config file)", err=True)
        sys.exit(1)

    # Git Provider Logic - Pre-check
    org = git_organization if git_organization else project_name
    repo_name = f"{application_name}-gitops"
    
    provider = get_git_provider(git_provider, git_token, server=git_server, organization=org, project=project_name)
    
    if provider.repo_exists(repo_name):
        click.echo(f"Repository {repo_name} already exists. Skipping.")
        sys.exit(0)

    # Template Selection
    match template_type:
        case 'dagster-platform':
            template_path = "/app/templates/gitops/luban-dagster-platform-gitops-template"
        case 'dagster-code-location':
            template_path = "/app/templates/gitops/luban-dagster-code-location-gitops-template"
        case 'standard':
            template_path = "/app/templates/gitops/luban-gitops-template"
        case _:
            # Fallback heuristic (Legacy support)
            if "dagster" in application_name:
                if "code-location" in application_name: 
                    template_path = "/app/templates/gitops/luban-dagster-code-location-gitops-template"
                else:
                    template_path = "/app/templates/gitops/luban-dagster-platform-gitops-template"
            else:
                 template_path = "/app/templates/gitops/luban-gitops-template"
    
    package_name = application_name.replace('-', '_')

    extra_context = {
        "project_name": project_name,
        "app_name": application_name,
        "package_name": package_name
    }
    
    # Merge entire config into extra_context to allow any arbitrary keys from config file
    # But ensure our explicit args override config
    for k, v in config.items():
        if k not in extra_context:
            extra_context[k] = v

    # Merge CLI extra context (takes precedence)
    extra_context.update(cli_extra_context)
    
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

    # Inflate Helm Chart if necessary (for Dagster Platform)
    # This logic detects if we used the dagster platform template and runs helm template
    repo_name = f"{application_name}-gitops"
    repo_dir = os.path.join(output_dir, repo_name)
    
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
