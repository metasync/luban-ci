from abc import ABC, abstractmethod

class GitProvider(ABC):
    """
    Abstract Base Class for Git Providers (GitHub, Azure DevOps, etc.)
    """

    def __init__(self, token, organization, project=None, git_server=None):
        self.token = token
        self.organization = organization
        self.project = project
        self.git_server = git_server

    @abstractmethod
    def repo_exists(self, repo_name):
        """Check if a repository exists."""
        pass

    @abstractmethod
    def create_repo(self, name, description=None):
        """Create a repository."""
        pass

    @abstractmethod
    def create_webhook(self, repo_identifier, webhook_url, secret=None):
        """Create a webhook for the repository."""
        pass

    @abstractmethod
    def set_default_branch(self, repo_identifier, branch_name):
        """Set the default branch."""
        pass

    @abstractmethod
    def enable_branch_protection(self, repo_identifier, branch_name, min_reviewers=1):
        """Enable branch protection."""
        pass

    @abstractmethod
    def create_project(self, project_name, description=None):
        """Ensure the Project/Organization exists."""
        pass

    @abstractmethod
    def create_pull_request(self, repo_identifier, title, description, source_ref, target_ref="main"):
        """Create a Pull Request."""
        pass
