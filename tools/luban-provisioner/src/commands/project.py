import os
import sys
import json
import shutil
import subprocess
import traceback
import click
from cookiecutter.main import cookiecutter
from utils import copy_secrets

@click.command(name='project')
@click.option('--project-name', required=True, help='Name of the project')
@click.option('--environment', required=True, help='Environment (snd/prd)')
@click.option('--git-org', required=True, help='Git Organization')
@click.option('--git-provider', default='github', help='Git Provider')
@click.option('--admin-groups', default='', help='Comma-separated list of admin groups')
@click.option('--developer-groups', default='', help='Comma-separated list of developer groups')
@click.option('--create-test-users', default='no', help='Create test service accounts (yes/no)')
@click.option('--image-pull-secret', required=True, help='Name of the image pull secret to copy and use')
@click.option('--dry-run', is_flag=True, help='Only generate files, do not apply')
def project(project_name, environment, git_org, git_provider, admin_groups, developer_groups, create_test_users, image_pull_secret, dry_run):
    """Bootstrap a new project namespace."""
    
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
    output_dir = '/tmp/luban-provisioner'
    
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

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
        subprocess.run(['kubectl', 'apply', '-f', generated_path, '--recursive'], check=True)
        click.echo("Manifests applied.")
    except subprocess.CalledProcessError as e:
        click.echo(f"Error applying manifests: {e}", err=True)
        sys.exit(1)

    # Copy Secrets logic
    copy_secrets(target_ns, "luban-ci", image_pull_secret)
