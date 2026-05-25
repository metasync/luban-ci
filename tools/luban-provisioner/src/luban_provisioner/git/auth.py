import base64
import os
import subprocess
from urllib.parse import urlsplit


def configure_git_https_auth(git_username, git_token, git_server):
    mode = (os.getenv("GIT_HTTPS_AUTH_MODE") or "credential_store").strip()
    if mode not in {"credential_store", "extraheader_basic"}:
        mode = "credential_store"
    if not git_username:
        git_username = "git"

    os.environ["GIT_TERMINAL_PROMPT"] = "0"

    if mode == "extraheader_basic":
        basic_user = (os.getenv("GIT_BASIC_AUTH_USERNAME") or git_username).strip()
        raw = f"{basic_user}:{git_token}".encode("utf-8")
        basic = base64.b64encode(raw).decode("ascii")
        os.environ["LUBAN_GIT_HTTPS_AUTH_MODE"] = "extraheader_basic"
        os.environ["LUBAN_GIT_AUTH_HEADER"] = f"Authorization: Basic {basic}"
        return

    os.environ["LUBAN_GIT_HTTPS_AUTH_MODE"] = "credential_store"
    os.environ.pop("LUBAN_GIT_AUTH_HEADER", None)

    if git_server and "://" in git_server:
        parts = urlsplit(git_server)
        if parts.netloc:
            git_server = parts.netloc
    git_server = (git_server or "").strip().strip("/")
    subprocess.run(["git", "config", "--global", "credential.helper", "store"], check=True)
    credentials_path = os.path.expanduser("~/.git-credentials")
    with open(credentials_path, "w", encoding="utf-8") as f:
        f.write(f"https://{git_username}:{git_token}@{git_server}\n")


def apply_git_https_config(config: dict, git_provider: str, git_server: str):
    config = config or {}

    env_mode = (os.getenv("GIT_HTTPS_AUTH_MODE") or "").strip()
    env_base_url = (os.getenv("GIT_BASE_URL") or "").strip()
    env_basic_user = (os.getenv("GIT_BASIC_AUTH_USERNAME") or "").strip()

    base_url = env_base_url or config.get(f"{git_provider}_base_url")

    mode = env_mode or config.get(f"{git_provider}_https_auth_mode")
    if not mode:
        mode = "credential_store"
    if str(mode).strip() not in {"credential_store", "extraheader_basic"}:
        mode = "credential_store"

    os.environ["GIT_HTTPS_AUTH_MODE"] = str(mode).strip()

    basic_user = env_basic_user or config.get(f"{git_provider}_basic_auth_username")
    if basic_user is not None and str(basic_user).strip() != "":
        os.environ["GIT_BASIC_AUTH_USERNAME"] = str(basic_user).strip()

    return base_url
