import os
import sys
import json
import shutil
import subprocess
import traceback
import click
from cookiecutter.main import cookiecutter
from luban_provisioner.utils import copy_secrets, copy_configmaps, patch_default_service_account

@click.command(name='k8s')
@click.option('--project-name', required=True, help='Name of the project')
@click.option('--environment', required=True, help='Environment (snd/prd)')
@click.option('--git-organization', required=True, help='Git Organization (for templates)')
@click.option('--git-provider', default='github', help='Git Provider (for templates)')
@click.option('--admin-group', default='', help='AD Group for Project Admins')
@click.option('--developer-group', default='', help='AD Group for Project Developers')
@click.option('--image-pull-secret', required=True, help='Name of the image pull secret to copy and use')
@click.option('--dry-run', is_flag=True, help='Only generate files, do not apply')
def k8s(project_name, environment, git_organization, git_provider, admin_group, developer_group, image_pull_secret, dry_run):
    """Provision Kubernetes Namespace and Resources."""
    
    target_ns = f"{environment}-{project_name}"
    click.echo(f"Bootstrapping project {project_name} in {target_ns}...")

    # Context for Cookiecutter
    context = {
        "project_name": project_name,
        "environment": environment,
        "target_namespace": target_ns,
        "git_organization": git_organization,
        "git_provider": git_provider,
        "admin_group": admin_group,
        "developer_group": developer_group,
        "image_pull_secret": image_pull_secret
    }

    # Template directory
    template_dir = "/app/templates/project"
    
    # Use a temporary directory for output to avoid collisions/permissions issues
    import tempfile
    output_dir = tempfile.mkdtemp(prefix='luban-provisioner-')
    
    # Generate
    try:
        cookiecutter(
            template_dir,
            no_input=True,
            extra_context=context,
            output_dir=output_dir,
            overwrite_if_exists=True
        )
        click.echo("Manifests generated successfully.")
    except Exception as e:
        click.echo(f"Error generating manifests: {e}", err=True)
        traceback.print_exc()
        sys.exit(1)

    generated_path = os.path.join(output_dir, target_ns)

    if dry_run:
        click.echo(f"Dry run: Manifests generated at {generated_path}")
        subprocess.run(['find', generated_path], check=True)
        return

    # Apply manifests
    click.echo("Applying manifests to cluster...")
    try:
        # 1. Apply Namespace first to avoid race conditions
        ns_file = os.path.join(generated_path, "namespace.yaml")
        if os.path.exists(ns_file):
            click.echo(f"Applying Namespace {target_ns} first...")
            subprocess.run(['kubectl', 'apply', '-f', ns_file], check=True)
        
        # 2. Apply the rest
        subprocess.run(['kubectl', 'apply', '-f', generated_path, '--recursive'], check=True)
        click.echo("Manifests applied.")
    except subprocess.CalledProcessError as e:
        click.echo(f"Error applying manifests: {e}", err=True)
        sys.exit(1)

    # Copy Secrets logic
    # Note: We assume the secret exists in 'luban-ci' namespace.
    copy_secrets(target_ns, "luban-ci", image_pull_secret)
    
    # Copy ConfigMaps
    copy_configmaps(target_ns, "luban-ci")

    # Patch default service account to use image pull secret
    patch_default_service_account(target_ns, image_pull_secret)
