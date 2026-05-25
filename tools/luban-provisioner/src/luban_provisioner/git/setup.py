from luban_provisioner.git.auth import configure_git_https_auth
from luban_provisioner.git.repo import configure_git_identity


def prepare_git_https(git_username, git_token, git_server):
    configure_git_https_auth(git_username, git_token, git_server)
    configure_git_identity()
