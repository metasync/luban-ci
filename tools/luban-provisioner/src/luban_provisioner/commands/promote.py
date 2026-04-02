import os
import sys
import click
import tempfile
import subprocess
from ruamel.yaml import YAML
from luban_provisioner.provider_factory import get_git_provider, get_remote_url
from luban_provisioner.utils import configure_git_https_auth, configure_git_identity, run_git


def _select_image(images, app_name):
    if not images:
        return None

    if len(images) == 1:
        return images[0]

    suffix = f"/{app_name}"
    for image in images:
        name = image.get("name") or ""
        if name.endswith(suffix):
            return image

    for image in images:
        name = image.get("name") or ""
        if suffix in name:
            return image

    return images[0]

@click.command()
@click.option('--app-name', required=True, help='Application name')
@click.option('--git-organization', required=True, help='Git Organization')
@click.option('--git-provider', required=True, type=click.Choice(['github', 'azure', 'ado']), help='Git Provider')
@click.option('--git-username', required=False, envvar='GIT_USERNAME', default='git', help='Git Username (env: GIT_USERNAME)')
@click.option('--git-token', required=True, envvar='GIT_TOKEN', help='Git Token (env: GIT_TOKEN)')
@click.option('--git-server', required=True, envvar='GIT_SERVER', help='Git Server (env: GIT_SERVER)')
@click.option('--git-base-url', required=False, envvar='GIT_BASE_URL', default='', help='Git base URL (optional, supports path prefixes)')
@click.option('--project-name', required=True, help='Project Name (for Azure)')
def promote(app_name, git_organization, git_provider, git_username, git_token, git_server, git_base_url, project_name):
    """Promote an application from Sandbox (snd) to Production (prd)."""
    gitops_repo_name = f"{app_name}-gitops"

    org = git_organization if git_organization else project_name
    provider = get_git_provider(git_provider, git_token, server=git_server, organization=org, project=project_name, base_url=git_base_url)
    if not provider:
        click.echo(f"Unsupported git provider: {git_provider}", err=True)
        sys.exit(1)
    repo_url = get_remote_url(git_provider, git_token, git_server, org, project_name, gitops_repo_name, base_url=git_base_url)

    configure_git_https_auth(git_username, git_token, git_server)
    configure_git_identity()

    yaml = YAML()
    yaml.preserve_quotes = True

    snd_kust_rel = os.path.join("app", "overlays", "snd", "kustomization.yaml")
    prd_kust_rel = os.path.join("app", "overlays", "prd", "kustomization.yaml")

    with tempfile.TemporaryDirectory() as work_dir:
        click.echo(f"Cloning {repo_url} into {work_dir}...")
        try:
            run_git(["clone", "-b", "develop", repo_url, work_dir], check=True)
        except subprocess.CalledProcessError:
            click.echo("Failed to clone repository. Check credentials and URL.", err=True)
            sys.exit(1)

        cwd = os.getcwd()
        os.chdir(work_dir)
        try:
            if not os.path.exists(snd_kust_rel):
                click.echo(f"Error: {snd_kust_rel} not found.", err=True)
                sys.exit(1)

            with open(snd_kust_rel, "r", encoding="utf-8") as f:
                snd_data = yaml.load(f) or {}

            images = snd_data.get("images", [])
            selected = _select_image(images, app_name)
            if not selected:
                click.echo("Error: No images found in snd kustomization.yaml", err=True)
                sys.exit(1)

            target_image = selected.get("name")
            target_tag = selected.get("newTag")
            if not target_image or not target_tag:
                click.echo("Error: Could not extract name/newTag from snd images", err=True)
                sys.exit(1)

            click.echo(f"Promoting Image: {target_image}")
            click.echo(f"Promoting Tag:   {target_tag}")

            if not os.path.exists(prd_kust_rel):
                click.echo(f"Error: {prd_kust_rel} not found.", err=True)
                sys.exit(1)

            with open(prd_kust_rel, "r", encoding="utf-8") as f:
                prd_data = yaml.load(f) or {}

            prd_images = prd_data.get("images") or []
            found = False
            for img in prd_images:
                if img.get("name") == target_image:
                    img["newTag"] = target_tag
                    if "newName" in img:
                        del img["newName"]
                    found = True
                    break

            if not found:
                prd_images.append({"name": target_image, "newTag": target_tag})
                prd_data["images"] = prd_images

            with open(prd_kust_rel, "w", encoding="utf-8") as f:
                yaml.dump(prd_data, f)

            status = run_git(["status", "--porcelain"], capture_output=True, text=True, check=False)
            if not status.stdout.strip():
                click.echo("No changes to promote. PRD overlay is already up to date.")
                return

            commit_msg = f"Promote {app_name} to prd (tag: {target_tag})"
            run_git(["add", "."], check=True)
            run_git(["commit", "-m", commit_msg], check=True)
            run_git(["push", "origin", "develop"], check=True)

            pr_title = f"Promote {app_name} to prd ({target_tag})"
            pr_body = (
                "Automated promotion request from snd (develop) to prd (main).<br><br>"
                f"**App**: {app_name}<br>**Tag**: {target_tag}"
            )

            provider.create_pull_request(
                repo_identifier=gitops_repo_name,
                title=pr_title,
                description=pr_body,
                source_ref="develop",
                target_ref="main",
            )
        finally:
            os.chdir(cwd)
