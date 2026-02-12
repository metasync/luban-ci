import os
import sys
import json
import shutil
import subprocess
import traceback
import click
from cookiecutter.main import cookiecutter
from utils import copy_secrets, copy_configmaps, patch_default_service_account

@click.command(name='k8s')
@click.option('--project-name', required=True, help='Name of the project')
@click.option('--environment', required=True, help='Environment (snd/prd)')
@click.option('--git-org', required=True, help='Git Organization (for templates)')
@click.option('--git-provider', default='github', help='Git Provider (for templates)')
@click.option('--admin-groups', default='', help='Comma-separated list of admin groups')
@click.option('--developer-groups', default='', help='Comma-separated list of developer groups')
@click.option('--create-test-users', default='no', help='Create test service accounts (yes/no)')
@click.option('--image-pull-secret', required=True, help='Name of the image pull secret to copy and use')
@click.option('--dry-run', is_flag=True, help='Only generate files, do not apply')
def k8s(project_name, environment, git_org, git_provider, admin_groups, developer_groups, create_test_users, image_pull_secret, dry_run):
    """Provision Kubernetes Namespace and Resources."""
    
    target_ns = f"{environment}-{project_name}"
    click.echo(f"Bootstrapping project {project_name} in {target_ns}...")

    # Parse groups
    try:
        admins_list = json.loads(admin_groups) if admin_groups.startswith('[') else [g.strip() for g in admin_groups.split(',') if g.strip()]
    except json.JSONDecodeError:
        click.echo(f"Warning: Failed to parse admin_groups JSON: {admin_groups}", err=True)
        admins_list = []

    try:
        devs_list = json.loads(developer_groups) if developer_groups.startswith('[') else [g.strip() for g in developer_groups.split(',') if g.strip()]
    except json.JSONDecodeError:
        click.echo(f"Warning: Failed to parse developer_groups JSON: {developer_groups}", err=True)
        devs_list = []
    
    should_create_test_users = create_test_users.lower() == 'yes'

    # Context for Cookiecutter
    context = {
        "project_name": project_name,
        "environment": environment,
        "target_namespace": target_ns,
        "git_organization": git_org,
        "git_provider": git_provider,
        "admin_groups": ",".join(admins_list),
        "developer_groups": ",".join(devs_list),
        "create_test_users": "yes" if should_create_test_users else "no",
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

    # Also copy azure-creds/azure-ssh-creds if available?
    # The previous logic in utils.py copy_secrets might handle it if we pass it?
    # utils.py copy_secrets only copies the *specific* secret passed.
    # The 'project.py' didn't explicitly call copy_secrets for 'azure-creds',
    # but 'utils.py' has a method 'copy_secrets' which might have been updated by me earlier?
    # Let's check utils.py content.
    
    # But wait, in the previous 'project.py' (lines 163-164):
    # copy_secrets(target_ns, "luban-ci", image_pull_secret)
    # patch_default_service_account(target_ns, image_pull_secret)
    # It seems it only copied image_pull_secret.
    # Did I update utils.py to copy azure-creds?
    # Yes, I updated utils.py in a previous turn (Task 10) to copy azure-creds.
    # Let's double check utils.py to be sure.
    
    patch_default_service_account(target_ns, image_pull_secret)
