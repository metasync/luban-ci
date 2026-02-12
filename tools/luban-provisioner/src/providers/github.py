import os
import requests
import click
import json
from .base import GitProvider

class GitHubProvider(GitProvider):
    def __init__(self, token, organization, project=None, git_server="github.com"):
        super().__init__(token, organization, project, git_server)
        self.api_url = f"https://api.{git_server}" if git_server == "github.com" else f"https://{git_server}/api/v3"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def get_current_user(self):
        """Get the authenticated user's login."""
        resp = requests.get(f"{self.api_url}/user", headers=self.headers)
        if resp.status_code == 200:
            return resp.json().get("login")
        return None

    def repo_exists(self, repo_name):
        """Check if a repository exists."""
        # Check if repo_name contains slash (owner/repo) or if we should use self.organization
        if "/" in repo_name:
            owner, name = repo_name.split("/", 1)
        else:
            owner = self.organization
            name = repo_name

        resp = requests.get(f"{self.api_url}/repos/{owner}/{name}", headers=self.headers)
        return resp.status_code == 200

    def create_repo(self, name, description=None):
        """
        Create a repository. 
        If self.organization is provided, create in that org.
        If org creation fails (e.g. not an org), or org is not provided, try creating in user account.
        """
        payload = {
            "name": name,
            "private": True, # Default to private
            "auto_init": False
        }
        if description:
            payload["description"] = description

        # Try creating in Org
        if self.organization:
            click.echo(f"Attempting to create repo '{name}' in organization '{self.organization}'...")
            resp = requests.post(f"{self.api_url}/orgs/{self.organization}/repos", headers=self.headers, json=payload)
            
            if resp.status_code == 201:
                return resp.json()
            
            if resp.status_code == 404:
                click.echo(f"Organization '{self.organization}' not found or not accessible. Checking user account...")
            else:
                click.echo(f"Failed to create in org '{self.organization}'. Status: {resp.status_code}, Body: {resp.text}", err=True)
                # If it's a permission error or name collision, we might not want to fallback?
                # But existing script falls back if 404.
                if resp.status_code != 404:
                    return None

        # Fallback to User
        # Check if the intended org matches the current user
        current_user = self.get_current_user()
        if not current_user:
            click.echo("Could not determine current user.", err=True)
            return None

        if self.organization and self.organization != current_user:
             click.echo(f"Target '{self.organization}' is not the authenticated user '{current_user}'. Aborting fallback.", err=True)
             return None

        click.echo(f"Creating repo '{name}' for user '{current_user}'...")
        resp = requests.post(f"{self.api_url}/user/repos", headers=self.headers, json=payload)
        
        if resp.status_code == 201:
            return resp.json()
        
        click.echo(f"Failed to create repo for user. Status: {resp.status_code}, Body: {resp.text}", err=True)
        return None

    def create_webhook(self, repo_identifier, webhook_url, secret, events=["push"]):
        """Create a webhook for the repository."""
        # Ensure correct path
        target_url = f"{webhook_url}/github/push"
        
        # repo_identifier can be name (if using self.organization) or full 'owner/name'
        # But for API consistency, let's assume it's just the name if we have self.organization context
        if isinstance(repo_identifier, dict):
            repo_name = repo_identifier.get('name')
            owner = repo_identifier.get('owner', {}).get('login', self.organization)
        elif "/" in repo_identifier:
            owner, repo_name = repo_identifier.split("/", 1)
        else:
            owner = self.organization
            repo_name = repo_identifier

        # Check existing hooks
        hooks_url = f"{self.api_url}/repos/{owner}/{repo_name}/hooks"
        resp = requests.get(hooks_url, headers=self.headers)
        if resp.status_code == 200:
            hooks = resp.json()
            for hook in hooks:
                if hook.get("config", {}).get("url") == target_url:
                    click.echo("Webhook already exists.")
                    return hook

        # Create new hook
        config = {
            "url": target_url,
            "content_type": "json",
            "secret": secret,
            "insecure_ssl": "0"
        }
        payload = {
            "name": "web",
            "active": True,
            "events": events,
            "config": config
        }
        
        click.echo(f"Creating webhook for {owner}/{repo_name}...")
        resp = requests.post(hooks_url, headers=self.headers, json=payload)
        if resp.status_code == 201:
            return resp.json()
        
        click.echo(f"Failed to create webhook. Status: {resp.status_code}, Body: {resp.text}", err=True)
        return None

    def set_default_branch(self, repo_identifier, branch_name):
        """Set the default branch."""
        if isinstance(repo_identifier, dict):
            repo_name = repo_identifier.get('name')
            owner = repo_identifier.get('owner', {}).get('login', self.organization)
        elif "/" in repo_identifier:
            owner, repo_name = repo_identifier.split("/", 1)
        else:
            owner = self.organization
            repo_name = repo_identifier

        click.echo(f"Setting default branch to '{branch_name}'...")
        payload = {"default_branch": branch_name}
        resp = requests.patch(f"{self.api_url}/repos/{owner}/{repo_name}", headers=self.headers, json=payload)
        if resp.status_code != 200:
            click.echo(f"Failed to set default branch. Status: {resp.status_code}, Body: {resp.text}", err=True)
            return False
        return True

    def enable_branch_protection(self, repo_identifier, branch_name, min_reviewers=1):
        """Enable branch protection."""
        if isinstance(repo_identifier, dict):
            repo_name = repo_identifier.get('name')
            owner = repo_identifier.get('owner', {}).get('login', self.organization)
        elif "/" in repo_identifier:
            owner, repo_name = repo_identifier.split("/", 1)
        else:
            owner = self.organization
            repo_name = repo_identifier

        click.echo(f"Enabling branch protection for '{branch_name}'...")
        payload = {
            "required_status_checks": None,
            "enforce_admins": True,
            "required_pull_request_reviews": {
                "dismiss_stale_reviews": True,
                "require_code_owner_reviews": False,
                "required_approving_review_count": min_reviewers
            },
            "restrictions": None
        }
        
        url = f"{self.api_url}/repos/{owner}/{repo_name}/branches/{branch_name}/protection"
        resp = requests.put(url, headers=self.headers, json=payload)
        
        if resp.status_code != 200:
            click.echo(f"Failed to enable branch protection. Status: {resp.status_code}, Body: {resp.text}", err=True)
            return False
        return True

    def create_project(self, project_name, description=None):
        """
        Create a GitHub Project.
        This method is a no-op for GitHub in the context of creating a 'container for repos'.
        """
        click.echo(f"GitHub Provider: create_project is a no-op for '{project_name}'. Repositories are created directly under Organization/User.")
        return {"name": project_name, "status": "exists (virtual)"}

    def create_pull_request(self, repo_identifier, title, description, source_ref, target_ref="main"):
        """Create a Pull Request."""
        if isinstance(repo_identifier, dict):
            repo_name = repo_identifier.get('name')
            owner = repo_identifier.get('owner', {}).get('login', self.organization)
        elif "/" in repo_identifier:
            owner, repo_name = repo_identifier.split("/", 1)
        else:
            owner = self.organization
            repo_name = repo_identifier

        url = f"{self.api_url}/repos/{owner}/{repo_name}/pulls"
        
        payload = {
            "title": title,
            "body": description,
            "head": source_ref,
            "base": target_ref
        }
        
        click.echo(f"Creating PR '{title}' in {owner}/{repo_name}...")
        resp = requests.post(url, headers=self.headers, json=payload)
        
        if resp.status_code == 201:
            pr = resp.json()
            click.echo(f"✅ Pull Request created successfully! URL: {pr.get('html_url')}")
            return pr
        elif resp.status_code == 422:
            click.echo("⚠️ Pull Request might already exist or no changes found.")
            return None
        
        click.echo(f"❌ Error creating Pull Request. Status: {resp.status_code}, Body: {resp.text}", err=True)
        return None
