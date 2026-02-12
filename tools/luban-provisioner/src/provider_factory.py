import click
import sys
from providers.github import GitHubProvider
from providers.azure import AzureProvider

def get_git_provider(provider_name, token, server=None, organization=None, project=None):
    """
    Factory function to get the appropriate Git provider instance.
    """
    if provider_name == 'github':
        if not server:
            server = "github.com"
        return GitHubProvider(token, organization=organization, project=project, git_server=server)
    
    elif provider_name == 'azure':
        if not server:
            server = "dev.azure.com"
            
        # For Azure, we need organization and project
        # If organization is missing, we try to derive it or fail
        if not organization:
             # If project_name has a slash, maybe it's org/proj
            if project and "/" in project:
                organization, project = project.split("/", 1)
            else:
                click.echo("Error: git_organization is required for Azure DevOps.", err=True)
                sys.exit(1)

        return AzureProvider(token, organization=organization, project=project, git_server=server)
    
    else:
        click.echo(f"Unsupported git provider: {provider_name}", err=True)
        sys.exit(1)

def get_remote_url(provider_name, token, server, organization, project, repo_name):
    """
    Generate the remote URL based on the provider.
    """
    if provider_name == 'github':
        if not server:
            server = "github.com"
        return f"https://{token}@{server}/{organization}/{repo_name}.git"
    
    elif provider_name == 'azure':
        if not server:
            server = "dev.azure.com"
        # Azure DevOps URL format
        return f"https://git:{token}@{server}/{organization}/{project}/_git/{repo_name}"
    
    return ""
