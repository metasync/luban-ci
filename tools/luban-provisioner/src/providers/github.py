import os
import requests
import click
import json

class GitHubProvider:
    def __init__(self, token, git_server="github.com"):
        self.token = token
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
        # Ensure correct path
        target_url = f"{webhook_url}/github/push"
        
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

    def create_project(self, project_name, description=None):
        """
        Create a GitHub Project.
        For GitHub, 'Projects' are often organizational level or user level projects (V2/Beta).
        However, in the context of 'Git Project' vs 'Azure Project', GitHub doesn't strictly require
        a 'Project' container to hold repositories (Repositories belong to Users/Orgs).
        
        This method is a no-op for GitHub in the context of creating a 'container for repos' 
        because the Organization/User already exists.
        
        If we wanted to create a GitHub Project Board, we could do that, but likely out of scope for now.
        """
        click.echo(f"GitHub Provider: create_project is a no-op for '{project_name}'. Repositories are created directly under Organization/User.")
        return {"name": project_name, "status": "exists (virtual)"}

    def create_pull_request(self, owner, repo_name, title, body, head, base="main"):
        """Create a Pull Request."""
        url = f"{self.api_url}/repos/{owner}/{repo_name}/pulls"
        
        payload = {
            "title": title,
            "body": body,
            "head": head,
            "base": base
        }
        
        click.echo(f"Creating PR '{title}' in {owner}/{repo_name}...")
        resp = requests.post(url, headers=self.headers, json=payload)
        
        if resp.status_code == 201:
            pr = resp.json()
            click.echo(f"✅ Pull Request created successfully! URL: {pr.get('html_url')}")
            return pr
        elif resp.status_code == 422:
             click.echo("⚠️ Pull Request might already exist or no changes found.")
             # We might want to try to find the existing PR to return it?
             # For now just return None or the error.
             return None
        
        click.echo(f"❌ Error creating Pull Request. Status: {resp.status_code}, Body: {resp.text}", err=True)
        return None
