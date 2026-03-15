import os
import click
import subprocess
import shutil
import tempfile
from ruamel.yaml import YAML
from luban_provisioner.provider_factory import get_git_provider, get_remote_url
from luban_provisioner.utils import configure_git_https_auth, configure_git_identity

@click.group()
def dagster():
    """Dagster Platform Management Commands"""
    pass

@click.command(name='register-location')
@click.option('--platform-project', required=True, help='Platform Project Name')
@click.option('--platform-app', required=True, help='Platform Application Name')
@click.option('--environment', required=True, help='Target Environment (snd, prd)')
@click.option('--location-name', required=True, help='Name of the Code Location (usually the app name)')
@click.option('--location-host', required=True, help='Host/DNS of the Code Location Service')
@click.option('--location-port', required=True, default=4000, help='Port of the Code Location Service')
@click.option('--git-organization', required=True, help='Git Organization')
@click.option('--git-provider', required=True, help='Git Provider')
@click.option('--git-token', envvar='GIT_TOKEN', required=True, help='Git Token')
@click.option('--git-server', envvar='GIT_SERVER', required=True, help='Git Server')
def register_location(platform_project, platform_app, environment, location_name, location_host, location_port, git_organization, git_provider, git_token, git_server):
    """
    Register a Code Location in the Dagster Platform's workspace.yaml.
    """
    click.echo(f"Registering code location '{location_name}' in platform '{platform_app}' ({environment})...")

    configure_git_https_auth(git_token, git_server)
    configure_git_identity()

    # 2. Clone Platform GitOps Repo
    platform_repo_name = f"{platform_app}-gitops"
    org = git_organization if git_organization else platform_project
    repo_url = get_remote_url(git_provider, git_token, git_server, org, platform_project, platform_repo_name)
    
    work_dir = tempfile.mkdtemp()
    click.echo(f"Cloning {repo_url} into {work_dir}...")
    
    try:
        # Clone develop by default as we likely push to develop for SND and maybe PRD depending on flow
        # But for PRD setup, we might target main?
        # Let's follow the standard: changes go to 'develop' -> PR -> 'main'.
        # However, 'setup' workflow might want to write directly if allowed.
        # For simplicity in 'setup', we'll try to checkout 'develop'.
        subprocess.run(["git", "clone", "-b", "develop", repo_url, work_dir], check=True)
    except subprocess.CalledProcessError:
        click.echo("Failed to clone repository. Check credentials and URL.", err=True)
        # Clean up
        shutil.rmtree(work_dir)
        exit(1)

    cwd = os.getcwd()
    os.chdir(work_dir)

    try:
        # 3. Locate/Create Environment Overlay
        overlay_dir = os.path.join("app", "overlays", environment)
        workspace_file = os.path.join(overlay_dir, "dagster-workspace-cm.yaml")
        kustomization_file = os.path.join(overlay_dir, "kustomization.yaml")

        if not os.path.exists(overlay_dir):
            click.echo(f"Error: Environment overlay '{environment}' does not exist in platform repo.", err=True)
            exit(1)

        yaml = YAML()
        yaml.preserve_quotes = True

        # 4. Check/Create dagster-workspace-cm.yaml in overlay
        # If it doesn't exist, we need to create it and add it to kustomization
        if not os.path.exists(workspace_file):
            click.echo(f"Creating {workspace_file}...")
            # Create basic structure
            # We need to see what's in base to know if we are replacing or merging.
            # Usually, workspace is a replacement because it's a list of locations.
            
            # Read base to check structure if needed, but we'll just start fresh for the overlay
            # assuming we want to override the base entirely or extend it.
            # Best practice for workspace: Define all locations for the env in the env overlay.
            # But wait, if we have multiple code locations, we want to APPEND.
            
            # If the file doesn't exist in overlay, it means we are using base currently.
            # We should copy base content to overlay start with.
            base_workspace = os.path.join("app", "base", "dagster", "dagster-workspace-cm.yaml")
            if os.path.exists(base_workspace):
                shutil.copy(base_workspace, workspace_file)
            else:
                # Fallback if base is missing (unlikely)
                with open(workspace_file, 'w') as f:
                    f.write("load_from: []\n")
            
            # Update kustomization to use this generator/patch
            # We need to replace the base generator or patch it.
            # The template uses configMapGenerator with behavior: merge/replace?
            # Let's check kustomization.yaml
            
            with open(kustomization_file, 'r') as f:
                kust_data = yaml.load(f)
            
            # We need to ensure we are replacing the workspace configmap
            # The base defines:
            # configMapGenerator:
            #   - name: dagster-workspace
            #     files: [workspace.yaml=dagster-workspace-cm.yaml]
            
            # In overlay, we want to override this file content.
            # Standard Kustomize: redefine the generator with 'behavior: replace' or just same name?
            # If we define the same generator name in overlay, it merges/overrides depending on Kustomize version.
            # Safer: Use a patch or just redefine generator.
            
            # Let's check if configMapGenerator exists in overlay kust
            if 'configMapGenerator' not in kust_data:
                kust_data['configMapGenerator'] = []
            
            # Check if 'dagster-workspace' generator is already there
            gen_found = False
            for gen in kust_data['configMapGenerator']:
                if gen.get('name') == 'dagster-workspace':
                    gen_found = True
                    break
            
            if not gen_found:
                kust_data['configMapGenerator'].append({
                    'name': 'dagster-workspace',
                    'behavior': 'merge', # or replace
                    'files': ['workspace.yaml=dagster-workspace-cm.yaml']
                })
                
                with open(kustomization_file, 'w') as f:
                    yaml.dump(kust_data, f)

        # 5. Parse and Update Workspace Config
        with open(workspace_file, 'r') as f:
            workspace_data = yaml.load(f)

        if 'load_from' not in workspace_data:
            workspace_data['load_from'] = []

        # Check if location already exists
        exists = False
        for entry in workspace_data['load_from']:
            if 'grpc_server' in entry:
                if entry['grpc_server'].get('location_name') == location_name:
                    click.echo(f"Code location '{location_name}' already exists. Updating...")
                    entry['grpc_server']['host'] = location_host
                    entry['grpc_server']['port'] = location_port
                    exists = True
                    break
        
        if not exists:
            click.echo(f"Adding new code location '{location_name}'...")
            workspace_data['load_from'].append({
                'grpc_server': {
                    'host': location_host,
                    'port': location_port,
                    'location_name': location_name
                }
            })

        with open(workspace_file, 'w') as f:
            yaml.dump(workspace_data, f)

        # 6. Commit and Push
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
            click.echo("No changes to register.")
            return

        commit_msg = f"Register code location '{location_name}' in {environment}"
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        
        click.echo(f"Pushing to develop...")
        subprocess.run(["git", "push", "origin", "develop"], check=True)
        
        if environment == 'prd':
             click.echo("Environment is PRD. Creating Pull Request to merge changes to 'main'...")
             
             provider = get_git_provider(
                 git_provider, 
                 git_token, 
                 server=git_server, 
                 organization=org, 
                 project=platform_project
             )
             
             pr_title = f"Register Code Location: {location_name}"
             pr_body = (
                 f"Automated registration of Dagster Code Location '{location_name}'.\n\n"
                 f"**Environment**: {environment}\n"
                 f"**Service Host**: {location_host}\n"
                 f"**Service Port**: {location_port}\n"
             )
             
             try:
                 provider.create_pull_request(
                     repo_identifier=platform_repo_name,
                     title=pr_title,
                     description=pr_body,
                     source_ref="develop",
                     target_ref="main"
                 )
                 click.echo(f"Pull Request created successfully.")
             except Exception as pr_err:
                 click.echo(f"Warning: Failed to create Pull Request: {pr_err}", err=True)
                 # Don't fail the whole workflow, as the push to develop succeeded.

    except Exception as e:
        click.echo(f"Error registering location: {e}", err=True)
        exit(1)
    finally:
        os.chdir(cwd)
        shutil.rmtree(work_dir)

dagster.add_command(register_location)
