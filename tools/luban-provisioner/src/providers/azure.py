import requests
import click
import time
from .base import GitProvider

class AzureProvider(GitProvider):
    def __init__(self, token, organization, project, git_server="dev.azure.com"):
        super().__init__(token, organization, project, git_server)
        self.base_url = f"https://{git_server}/{organization}"
        self.auth = ('', self.token)

    def _get_project_id(self):
        """Get the ID of the Azure DevOps Project."""
        url = f"{self.base_url}/_apis/projects/{self.project}?api-version=7.1"
        resp = requests.get(url, auth=self.auth)
        if resp.status_code == 200:
            return resp.json().get('id')
        elif resp.status_code == 404:
            click.echo(f"Project '{self.project}' not found (404) at {url}", err=True)
            return None
        else:
            click.echo(f"Failed to check project existence. Status: {resp.status_code}, URL: {url}, Body: {resp.text}", err=True)
            return None

    def _get_repo_id(self, repo_identifier):
        """Helper to resolve repo ID from name or dict."""
        if isinstance(repo_identifier, dict):
            return repo_identifier.get('id')
        
        # If string, assume it's a name or ID. Try to fetch it.
        # GET /_apis/git/repositories/{repositoryId}
        url = f"{self.base_url}/{self.project}/_apis/git/repositories/{repo_identifier}?api-version=7.1"
        resp = requests.get(url, auth=self.auth)
        if resp.status_code == 200:
            return resp.json().get('id')
        return None

    def _get_policy_type_id(self, display_name):
        """Get policy type ID by display name."""
        url = f"{self.base_url}/{self.project}/_apis/policy/types?api-version=7.1"
        resp = requests.get(url, auth=self.auth)
        if resp.status_code == 200:
            types = resp.json().get("value", [])
            for t in types:
                if t.get("displayName") == display_name:
                    return t.get("id")
        return None

    def repo_exists(self, repo_name):
        """Check if a repository exists."""
        # Azure DevOps API: GET /_apis/git/repositories/{repositoryId}
        url = f"{self.base_url}/{self.project}/_apis/git/repositories/{repo_name}?api-version=7.1"
        resp = requests.get(url, auth=self.auth)
        return resp.status_code == 200

    def create_repo(self, name, description=None):
        """Create a repository."""
        url = f"{self.base_url}/{self.project}/_apis/git/repositories?api-version=7.1"
        
        project_id = self._get_project_id()
        if not project_id:
            click.echo(f"Project '{self.project}' not found.", err=True)
            return None

        payload = {
            "name": name,
            "project": {
                "id": project_id
            }
        }
        
        click.echo(f"Creating repo '{name}' in project '{self.project}'...")
        resp = requests.post(url, json=payload, auth=self.auth)
        
        if resp.status_code == 201:
            repo_data = resp.json()
            return repo_data
        
        click.echo(f"Failed to create repo. Status: {resp.status_code}, Body: {resp.text}", err=True)
        return None

    def create_webhook(self, repo_identifier, webhook_url, secret=None):
        """Create a Service Hook for Git Push."""
        repo_id = self._get_repo_id(repo_identifier)
        if not repo_id:
            click.echo("Failed to resolve repository ID for webhook creation.", err=True)
            return None

        url = f"{self.base_url}/_apis/hooks/subscriptions?api-version=7.1"
        project_id = self._get_project_id()
        
        consumer_inputs = {
            "url": f"{webhook_url}/azure/push"
        }
        
        if secret:
            consumer_inputs["httpHeaders"] = f"Authorization: {secret}"

        payload = {
            "publisherId": "tfs",
            "eventType": "git.push",
            "resourceVersion": "1.0",
            "consumerId": "webHooks",
            "consumerActionId": "httpRequest",
            "publisherInputs": {
                "repository": repo_id,
                "branch": "", # All branches
                "projectId": project_id
            },
            "consumerInputs": consumer_inputs
        }
        
        # Check existing hooks
        list_url = f"{self.base_url}/_apis/hooks/subscriptions?publisherId=tfs&eventType=git.push&api-version=7.1"
        list_resp = requests.get(list_url, auth=self.auth)
        if list_resp.status_code == 200:
            subs = list_resp.json().get("value", [])
            for sub in subs:
                if (sub.get("consumerInputs", {}).get("url") == f"{webhook_url}/azure/push" and 
                    sub.get("publisherInputs", {}).get("repository") == repo_id):
                    click.echo("Webhook already exists.")
                    return sub

        click.echo(f"Creating webhook for repo {repo_id}...")
        resp = requests.post(url, json=payload, auth=self.auth)
        
        if resp.status_code == 200: 
            return resp.json()
            
        click.echo(f"Failed to create webhook. Status: {resp.status_code}, Body: {resp.text}", err=True)
        return None

    def set_default_branch(self, repo_identifier, branch_name):
        """Set the default branch."""
        repo_id = self._get_repo_id(repo_identifier)
        if not repo_id:
            return False

        url = f"{self.base_url}/{self.project}/_apis/git/repositories/{repo_id}?api-version=7.1"
        
        payload = {
            "defaultBranch": f"refs/heads/{branch_name}"
        }
        
        click.echo(f"Setting default branch to '{branch_name}'...")
        resp = requests.patch(url, json=payload, auth=self.auth)
        
        if resp.status_code != 200:
            click.echo(f"Failed to set default branch. Status: {resp.status_code}, Body: {resp.text}", err=True)
            return False
        return True

    def enable_branch_protection(self, repo_identifier, branch_name, min_reviewers=1):
        """Enable branch policy (Min Reviewers)."""
        repo_id = self._get_repo_id(repo_identifier)
        if not repo_id:
            return False

        url = f"{self.base_url}/{self.project}/_apis/policy/configurations?api-version=7.1"
        
        min_reviewer_policy_id = self._get_policy_type_id("Minimum number of reviewers")
        
        if not min_reviewer_policy_id:
            click.echo("Warning: Could not find policy type 'Minimum number of reviewers'. Using default ID.", err=True)
            min_reviewer_policy_id = "fa4e907d-9e6b-4f87-9517-005e952ddf48"
        
        payload = {
            "isEnabled": True,
            "isBlocking": True,
            "type": {
                "id": min_reviewer_policy_id
            },
            "settings": {
                "minimumApproverCount": min_reviewers,
                "creatorVoteCounts": True,
                "scope": [
                    {
                        "repositoryId": repo_id,
                        "refName": f"refs/heads/{branch_name}",
                        "matchKind": "Exact"
                    }
                ]
            }
        }
        
        click.echo(f"Enabling branch protection (Min Reviewers={min_reviewers}) for '{branch_name}'...")
        resp = requests.post(url, json=payload, auth=self.auth)
        
        if resp.status_code in [200, 201]:
            return True
            
        click.echo(f"Failed to enable branch protection. Status: {resp.status_code}, Body: {resp.text}", err=True)
        return False

    def create_project(self, project_name, description=None):
        """
        Create an Azure DevOps Project.
        """
        # Check if project exists
        check_url = f"{self.base_url}/_apis/projects/{project_name}?api-version=7.1"
        check_resp = requests.get(check_url, auth=self.auth)
        
        if check_resp.status_code == 200:
            click.echo(f"Project '{project_name}' already exists.")
            return check_resp.json()
            
        # Create Project
        url = f"{self.base_url}/_apis/projects?api-version=7.1"
        
        payload = {
            "name": project_name,
            "description": description if description else f"Project {project_name} created by Luban Provisioner",
            "visibility": "private", 
            "capabilities": {
                "versioncontrol": {
                    "sourceControlType": "Git"
                },
                "processTemplate": {
                    "templateTypeId": "6b724908-ef14-45cf-84f8-768b5384da45" # Agile default
                }
            }
        }
        
        # Try to find Agile template
        process_url = f"{self.base_url}/_apis/process/processes?api-version=7.1"
        process_resp = requests.get(process_url, auth=self.auth)
        if process_resp.status_code == 200:
            processes = process_resp.json().get("value", [])
            agile_template = next((p for p in processes if p["name"] == "Agile"), None)
            if agile_template:
                payload["capabilities"]["processTemplate"]["templateTypeId"] = agile_template["id"]
            elif processes:
                payload["capabilities"]["processTemplate"]["templateTypeId"] = processes[0]["id"]
        
        click.echo(f"Creating Azure DevOps Project '{project_name}'...")
        resp = requests.post(url, json=payload, auth=self.auth)
        
        if resp.status_code == 202:
            operation_ref = resp.json()
            op_id = operation_ref.get('id')
            click.echo(f"Project creation queued. Operation ID: {op_id}")
            
            for _ in range(30):
                time.sleep(2)
                if self._get_project_id():
                    click.echo(f"Project '{project_name}' created successfully.")
                    return operation_ref
                
            click.echo(f"Timeout waiting for project '{project_name}' to be ready.", err=True)
            return operation_ref
            
        click.echo(f"Failed to create project. Status: {resp.status_code}, Body: {resp.text}", err=True)
        return None

    def create_pull_request(self, repo_identifier, title, description, source_ref, target_ref="main"):
        """Create a Pull Request."""
        repo_id = self._get_repo_id(repo_identifier)
        if not repo_id:
            return None

        url = f"{self.base_url}/{self.project}/_apis/git/repositories/{repo_id}/pullRequests?api-version=7.1"
        
        payload = {
            "sourceRefName": f"refs/heads/{source_ref}" if not source_ref.startswith("refs/") else source_ref,
            "targetRefName": f"refs/heads/{target_ref}" if not target_ref.startswith("refs/") else target_ref,
            "title": title,
            "description": description
        }
        
        click.echo(f"Creating PR '{title}' in {self.project} (Repo ID: {repo_id})...")
        resp = requests.post(url, json=payload, auth=self.auth)
        
        if resp.status_code == 201:
            pr = resp.json()
            click.echo(f"✅ Pull Request created successfully! ID: {pr.get('pullRequestId')}")
            return pr
        elif resp.status_code == 409: 
             click.echo("⚠️ Pull Request might already exist or conflict.")
             return None
             
        click.echo(f"❌ Error creating Pull Request. Status: {resp.status_code}, Body: {resp.text}", err=True)
        return None
