import sys
import os
import click
from cookiecutter.main import cookiecutter

@click.command(name='source')
@click.option('--project-name', required=True, help='Name of the project (e.g., team name)')
@click.option('--application-name', required=True, help='Name of the application')
@click.option('--output-dir', required=True, help='Directory to output the rendered template')
def source(project_name, application_name, output_dir):
    """Provision Source Code Repository"""
    
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
