import sys
import os
import click
from cookiecutter.main import cookiecutter

@click.command(name='gitops')
@click.option('--project-name', required=True, help='Name of the project/repo')
@click.option('--application-name', required=True, help='Name of the application')
@click.option('--output-dir', required=True, help='Directory to output the rendered template')
@click.option('--container-port', required=True, help='Port exposed by the container')
@click.option('--service-port', required=True, help='Port exposed by the service')
@click.option('--domain-suffix', required=True, help='Domain suffix for ingress/routes')
@click.option('--default-image-name', required=False, help='Default image name')
@click.option('--default-image-tag', required=False, help='Default image tag')
def gitops(project_name, application_name, output_dir, container_port, service_port, domain_suffix, default_image_name, default_image_tag):
    """Provision GitOps Repository"""
    
    # Template path in the new image structure
    # Assuming /app is the WORKDIR and templates are copied to /app/templates
    template_path = "/app/templates/gitops/luban-gitops-template"
    
    # Build context
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
        click.echo(f"Successfully generated template in {output_dir}/{application_name}-gitops")
    except Exception as e:
        click.echo(f"Error generating template: {e}", err=True)
        sys.exit(1)
