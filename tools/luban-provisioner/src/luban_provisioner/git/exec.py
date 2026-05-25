import os
import subprocess
from urllib.parse import urlsplit, urlunsplit


def run_git(args, cwd=None, check=True, capture_output=False, text=True):
    env = os.environ.copy()
    env.setdefault("GIT_TERMINAL_PROMPT", "0")

    cmd = ["git"]
    if env.get("LUBAN_GIT_HTTPS_AUTH_MODE") == "extraheader_basic" and env.get(
        "LUBAN_GIT_AUTH_HEADER"
    ):
        cmd.extend(["--config-env=http.extraHeader=LUBAN_GIT_AUTH_HEADER"])

    cmd.extend(args)
    return subprocess.run(
        cmd, cwd=cwd, env=env, check=check, capture_output=capture_output, text=text
    )


def redact_url(url: str) -> str:
    try:
        parts = urlsplit(url)
        if "@" not in parts.netloc:
            return url
        host = parts.netloc.split("@", 1)[1]
        return urlunsplit((parts.scheme, host, parts.path, parts.query, parts.fragment))
    except Exception:
        return "<redacted>"
