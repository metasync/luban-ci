import os
import click
import shutil
import tempfile
import subprocess
from ruamel.yaml import YAML
from provider_factory import get_git_provider, get_remote_url

@click.command()
@click.option('--app-name', required=True, help='Application name')
@click.option('--git-organization', required=True, help='Git Organization')
@click.option('--git-provider', required=True, type=click.Choice(['github', 'azure']), help='Git Provider')
@click.option('--git-token', required=True, envvar='GIT_TOKEN', help='Git Token (env: GIT_TOKEN)')
@click.option('--git-server', required=True, envvar='GIT_SERVER', help='Git Server (env: GIT_SERVER)')
@click.option('--project-name', required=True, help='Project Name (for Azure)')
def promote(app_name, git_organization, git_provider, git_token, git_server, project_name):
    """
    Promote an application from Sandbox (snd) to Production (prd).
    1. Clone GitOps repo.
    2. Extract tag from snd overlay.
    3. Update prd overlay.
    4. Commit and Push.
    5. Create Pull Request.
    """
    # 1. Determine GitOps Repo URL and Provider
    gitops_repo_name = f"{app_name}-gitops"
    
    # Provider Initialization
    # Logic for Azure Organization vs Project
    # We assume 'git_organization' corresponds to Azure Organization
    # and 'project_name' corresponds to Azure Project.
    
    org = git_organization if git_organization else project_name
    provider = get_git_provider(git_provider, git_token, server=git_server, organization=org, project=project_name)
    repo_url = get_remote_url(git_provider, git_token, git_server, org, project_name, gitops_repo_name)
    
    # Configure Git Creds for HTTPS
    subprocess.run(["git", "config", "--global", "credential.helper", "store"], check=True)
    with open(os.path.expanduser("~/.git-credentials"), "w") as f:
        f.write(f"https://git:{git_token}@{git_server}\n")

    # Git Config
    subprocess.run(["git", "config", "--global", "user.email", "ci@luban.com"], check=True)
    subprocess.run(["git", "config", "--global", "user.name", "Luban CI"], check=True)
    subprocess.run(["git", "config", "--global", "--add", "safe.directory", "*"], check=True)

    # 2. Clone Repository
    work_dir = tempfile.mkdtemp()
    click.echo(f"Cloning {repo_url} into {work_dir}...")
    try:
        subprocess.run(["git", "clone", "-b", "develop", repo_url, work_dir], check=True)
    except subprocess.CalledProcessError:
        click.echo("Failed to clone repository. Check credentials and URL.", err=True)
        exit(1)
        
    os.chdir(work_dir)
    
    # 3. Extract Tag from SND
    snd_kust = "app/overlays/snd/kustomization.yaml"
    prd_kust = "app/overlays/prd/kustomization.yaml"
    
    if not os.path.exists(snd_kust):
        click.echo(f"Error: {snd_kust} not found.", err=True)
        exit(1)
        
    # Use yq (subprocess) to extract tag. 
    # We use 'ruamel.yaml' for editing to preserve comments, but yq/jq is fine for reading.
    # Actually, let's use ruamel.yaml for everything to be consistent and avoid yq binary dependency if not needed,
    # BUT we added ruamel.yaml to Dockerfile.
    
    from ruamel.yaml import YAML
    yaml = YAML()
    yaml.preserve_quotes = True
    
    with open(snd_kust, 'r') as f:
        snd_data = yaml.load(f)
        
    # Assuming structure: images: [{name: ..., newTag: ...}]
    # We find the image matching app_name or the first one if we can't match?
    # The shell script extracted the FIRST image's newTag.
    # Let's try to match app_name if possible, or fallback to first.
    
    target_image = None
    target_tag = None
    
    images = snd_data.get('images', [])
    if not images:
        click.echo("Error: No images found in snd kustomization.yaml", err=True)
        exit(1)
        
    # Try to find specific app image? 
    # The shell script logic: APP_IMAGE_NAME=$(yq '.images[0].name' ...)
    # It just took the first one. We should replicate that behavior or improve it.
    # Let's replicate for now.
    
    first_image = images[0]
    target_image = first_image.get('name')
    target_tag = first_image.get('newTag')
    
    if not target_tag:
        click.echo("Error: Could not extract newTag from first image in snd.", err=True)
        exit(1)
        
    click.echo(f"Promoting Image: {target_image}")
    click.echo(f"Promoting Tag:   {target_tag}")
    
    # 4. Update PRD Overlay
    if not os.path.exists(prd_kust):
        click.echo(f"Error: {prd_kust} not found.", err=True)
        exit(1)
        
    with open(prd_kust, 'r') as f:
        prd_data = yaml.load(f)
        
    # Update logic
    prd_images = prd_data.get('images', [])
    found = False
    for img in prd_images:
        if img.get('name') == target_image:
            img['newTag'] = target_tag
            if 'newName' in img:
                del img['newName']
            found = True
            break
            
    if not found:
        click.echo("Image entry not found in PRD overlay. Appending...")
        prd_images.append({'name': target_image, 'newTag': target_tag})
        prd_data['images'] = prd_images # Ensure it's assigned back if it was None
        
    with open(prd_kust, 'w') as f:
        yaml.dump(prd_data, f)
        
    # 5. Commit and Push
    # Check for changes
    status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if not status.stdout.strip():
        click.echo("No changes to promote. PRD overlay is already up to date.")
        return

    commit_msg = f"Promote {app_name} to prd (tag: {target_tag})"
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", commit_msg], check=True)
    subprocess.run(["git", "push", "origin", "develop"], check=True)
    
    # 6. Create Pull Request
    pr_title = f"Promote {app_name} to prd ({target_tag})"
    pr_body = f"Automated promotion request from snd (develop) to prd (main).<br><br>**App**: {app_name}<br>**Tag**: {target_tag}"
    
    provider.create_pull_request(
        repo_identifier=gitops_repo_name,
        title=pr_title,
        description=pr_body,
        source_ref="develop",
        target_ref="main"
    )
