import click
import sys
from urllib.parse import urlsplit
from luban_provisioner.providers.github import GitHubProvider
from luban_provisioner.providers.azure import AzureProvider
from luban_provisioner.providers.ado import AdoProvider


def _normalize_git_server(server):
    if not server:
        return server
    server = server.strip()
    if "://" in server:
        parts = urlsplit(server)
        if parts.netloc:
            server = parts.netloc
    return server.strip("/")


def _normalize_git_base_url(base_url):
    if not base_url:
        return None
    base_url = str(base_url).strip().strip("/")
    if not base_url:
        return None
    if "://" not in base_url:
        base_url = f"https://{base_url}"
    return base_url.rstrip("/")

def get_git_provider(provider_name, token, server=None, organization=None, project=None, base_url=None):
    """
    Factory function to get the appropriate Git provider instance.
    """
    if provider_name == 'github':
        if not server:
            server = "github.com"
        server = _normalize_git_server(server)
        return GitHubProvider(token, organization=organization, project=project, git_server=server)
    
    elif provider_name == 'azure':
        if not server:
            server = "dev.azure.com"
        server = _normalize_git_server(server)

        base_url = _normalize_git_base_url(base_url)
            
        # For Azure, we need organization and project
        # If organization is missing, we try to derive it or fail
        if not organization:
             # If project_name has a slash, maybe it's org/proj
            if project and "/" in project:
                organization, project = project.split("/", 1)
            else:
                click.echo("Error: git_organization is required for Azure DevOps.", err=True)
                sys.exit(1)

        return AzureProvider(token, organization=organization, project=project, git_server=server, git_base_url=base_url)

    elif provider_name == 'ado':
        server = _normalize_git_server(server)
        base_url = _normalize_git_base_url(base_url)

        if not server and not base_url:
            click.echo("Error: git_server or git_base_url is required for Azure DevOps Server.", err=True)
            sys.exit(1)

        if server and (server == "dev.azure.com" or server.endswith(".visualstudio.com")):
            click.echo("Error: git_provider=ado does not support Azure DevOps Services hosts (dev.azure.com / *.visualstudio.com). Use git_provider=azure.", err=True)
            sys.exit(1)

        if not organization:
            if project and "/" in project:
                organization, project = project.split("/", 1)
            else:
                click.echo("Error: git_organization is required for Azure DevOps Server.", err=True)
                sys.exit(1)

        return AdoProvider(token, organization=organization, project=project, git_server=server, git_base_url=base_url)
    
    else:
        click.echo(f"Unsupported git provider: {provider_name}", err=True)
        sys.exit(1)

def get_remote_url(provider_name, _token, server, organization, project, repo_name, base_url=None):
    """
    Generate the remote URL based on the provider.
    """
    if provider_name == 'github':
        if not server:
            server = "github.com"
        server = _normalize_git_server(server)
        base = _normalize_git_base_url(base_url) or f"https://{server}"
        return f"{base}/{organization}/{repo_name}.git"
    
    elif provider_name == 'azure':
        if not server:
            server = "dev.azure.com"
        server = _normalize_git_server(server)
        base = _normalize_git_base_url(base_url) or f"https://{server}"
        return f"{base}/{organization}/{project}/_git/{repo_name}"

    elif provider_name == 'ado':
        server = _normalize_git_server(server)
        base = _normalize_git_base_url(base_url) or (f"https://{server}" if server else None)
        if not base:
            return ""
        return f"{base}/{organization}/{project}/_git/{repo_name}"
    
    return ""
