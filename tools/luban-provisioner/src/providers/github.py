import os
import requests
import click
import json

class GitHubProvider:
    def __init__(self, token):
        self.token = token
        self.api_url = "https://api.github.com"
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

    def repo_exists(self, owner, repo_name):
        """Check if a repository exists."""
        resp = requests.get(f"{self.api_url}/repos/{owner}/{repo_name}", headers=self.headers)
        return resp.status_code == 200

    def create_repo(self, name, org=None, private=False, description=None):
        """
        Create a repository. 
        If org is provided, create in that org.
        If org creation fails (e.g. not an org), or org is not provided, try creating in user account.
        """
        payload = {
            "name": name,
            "private": private,
            "auto_init": False
        }
        if description:
            payload["description"] = description

        # Try creating in Org
        if org:
            click.echo(f"Attempting to create repo '{name}' in organization '{org}'...")
            resp = requests.post(f"{self.api_url}/orgs/{org}/repos", headers=self.headers, json=payload)
            
            if resp.status_code == 201:
                return resp.json()
            
            if resp.status_code == 404:
                click.echo(f"Organization '{org}' not found or not accessible. Checking user account...")
            else:
                click.echo(f"Failed to create in org '{org}'. Status: {resp.status_code}, Body: {resp.text}", err=True)
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

        if org and org != current_user:
             click.echo(f"Target '{org}' is not the authenticated user '{current_user}'. Aborting fallback.", err=True)
             return None

        click.echo(f"Creating repo '{name}' for user '{current_user}'...")
        resp = requests.post(f"{self.api_url}/user/repos", headers=self.headers, json=payload)
        
        if resp.status_code == 201:
            return resp.json()
        
        click.echo(f"Failed to create repo for user. Status: {resp.status_code}, Body: {resp.text}", err=True)
        return None

    def create_webhook(self, owner, repo_name, webhook_url, secret, events=["push"]):
        """Create a webhook for the repository."""
        # Check existing hooks
        hooks_url = f"{self.api_url}/repos/{owner}/{repo_name}/hooks"
        resp = requests.get(hooks_url, headers=self.headers)
        if resp.status_code == 200:
            hooks = resp.json()
            for hook in hooks:
                if hook.get("config", {}).get("url") == webhook_url:
                    click.echo("Webhook already exists.")
                    return hook

        # Create new hook
        config = {
            "url": webhook_url,
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

    def set_default_branch(self, owner, repo_name, branch_name):
        """Set the default branch."""
        click.echo(f"Setting default branch to '{branch_name}'...")
        payload = {"default_branch": branch_name}
        resp = requests.patch(f"{self.api_url}/repos/{owner}/{repo_name}", headers=self.headers, json=payload)
        if resp.status_code != 200:
            click.echo(f"Failed to set default branch. Status: {resp.status_code}, Body: {resp.text}", err=True)
            return False
        return True

    def enable_branch_protection(self, owner, repo_name, branch_name, required_reviews=1):
        """Enable branch protection."""
        click.echo(f"Enabling branch protection for '{branch_name}'...")
        payload = {
            "required_status_checks": None,
            "enforce_admins": True,
            "required_pull_request_reviews": {
                "dismiss_stale_reviews": True,
                "require_code_owner_reviews": False,
                "required_approving_review_count": required_reviews
            },
            "restrictions": None
        }
        
        url = f"{self.api_url}/repos/{owner}/{repo_name}/branches/{branch_name}/protection"
        resp = requests.put(url, headers=self.headers, json=payload)
        
        if resp.status_code != 200:
            click.echo(f"Failed to enable branch protection. Status: {resp.status_code}, Body: {resp.text}", err=True)
            return False
        return True
