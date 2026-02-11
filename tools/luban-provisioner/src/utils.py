import subprocess
import click
import os

def copy_secrets(target_ns, source_ns, image_pull_secret):
    """
    Copies secrets from source namespace to target namespace.
    Specifically handles image pull secrets and harbor credentials.
    """
    secrets = ["github-creds"]
    if image_pull_secret:
        secrets.append(image_pull_secret)
    
    # Always try to copy harbor-creds (RW) for Kpack builds
    # This ensures workflow-runner has write access even if image_pull_secret is RO
    if image_pull_secret != "harbor-creds":
        secrets.append("harbor-creds")
        
    # Copy Azure SSH creds if available (always copy to be safe, or make it conditional?)
    # Since we might use Azure, let's copy it. It's harmless if unused.
    secrets.append("azure-ssh-creds")
    
    # Also copy azure-creds (HTTPS PAT) for GitOps updates which use HTTPS
    secrets.append("azure-creds")
    
    for secret in secrets:
        click.echo(f"Copying secret {secret} from {source_ns} to {target_ns}...")
        # check if exists in source
        check = subprocess.run(
            ['kubectl', 'get', 'secret', secret, '-n', source_ns], 
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        if check.returncode != 0:
            click.echo(f"Warning: Secret {secret} not found in {source_ns}, skipping.")
            continue

        # Get and Apply using jq
        # Note: we assume jq is installed in the container
        cmd = f"kubectl get secret {secret} -n {source_ns} -o json | " \
              f"jq 'del(.metadata.namespace,.metadata.resourceVersion,.metadata.uid,.metadata.creationTimestamp)' | " \
              f"kubectl apply -n {target_ns} -f -"
        
        try:
            subprocess.run(cmd, shell=True, check=True)
        except subprocess.CalledProcessError:
            click.echo(f"Failed to copy secret {secret}", err=True)

def initialize_git_repo(repo_dir, remote_url, user_name="Luban CI", user_email="luban-ci@metasync.io", initial_branch="main"):
    """Initialize a git repository, commit all files, and push to remote."""
    cwd = os.getcwd()
    try:
        os.chdir(repo_dir)
        
        click.echo(f"Initializing git repo in {repo_dir}...")
        
        # Init
        subprocess.run(["git", "init"], check=True)
        subprocess.run(["git", "config", "user.name", user_name], check=True)
        subprocess.run(["git", "config", "user.email", user_email], check=True)
        subprocess.run(["git", "config", "--add", "safe.directory", "*"], check=True)
        
        # Branch
        subprocess.run(["git", "branch", "-M", initial_branch], check=True)
        
        # Add and Commit
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Initial provisioning"], check=True)
        
        # Remote
        subprocess.run(["git", "remote", "add", "origin", remote_url], check=True)
        
        # Push
        click.echo(f"Pushing to {initial_branch}...")
        subprocess.run(["git", "push", "-u", "origin", initial_branch, "--force"], check=True)
        
    except subprocess.CalledProcessError as e:
        click.echo(f"Git operation failed: {e}", err=True)
        raise e
def patch_default_service_account(target_ns, image_pull_secret):
    """Patch the default service account to use the image pull secret."""
    if not image_pull_secret:
        return
        
    click.echo(f"Patching default service account in {target_ns} with {image_pull_secret}...")
    patch_json = f'{{"imagePullSecrets": [{{"name": "{image_pull_secret}"}}]}}'
    cmd = ['kubectl', 'patch', 'serviceaccount', 'default', '-n', target_ns, '-p', patch_json]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
        click.echo("Default service account patched.")
    except subprocess.CalledProcessError as e:
        click.echo(f"Failed to patch default service account: {e}", err=True)

def create_and_push_branch(repo_dir, branch_name):
    """Create a new branch and push it."""
    cwd = os.getcwd()
    try:
        os.chdir(repo_dir)
        click.echo(f"Creating and pushing branch {branch_name}...")
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)
        subprocess.run(["git", "push", "-u", "origin", branch_name, "--force"], check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Git branch operation failed: {e}", err=True)
        raise e
    finally:
        os.chdir(cwd)
