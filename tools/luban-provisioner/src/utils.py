import subprocess
import click

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
