from luban_provisioner.providers.azure import AzureProvider


class AdoProvider(AzureProvider):
    """Azure DevOps Server (on-prem) provider.

    This currently reuses the Azure DevOps REST implementation but is kept as a
    separate provider class to support on-prem specific behavior over time.
    """

    def __init__(self, token, organization, project, git_server=None, git_base_url=None):
        super().__init__(
            token, organization, project, git_server=git_server or "", git_base_url=git_base_url
        )

    def webhook_push_path(self) -> str:
        return "/ado/push"
