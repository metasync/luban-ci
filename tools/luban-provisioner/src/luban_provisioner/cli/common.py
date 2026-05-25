import os
import re

import click


def parse_set_overrides(set_values):
    overrides = {}
    for item in set_values or []:
        if "=" in item:
            key, value = item.split("=", 1)
            overrides[key] = value
        else:
            click.echo(f"Warning: Invalid set option '{item}'. Must be key=value", err=True)
    return overrides


_SENSITIVE_KEY_RE = re.compile(
    r"(token|secret|password|passphrase|private[_-]?key|api[_-]?key)", re.I
)


def format_context_for_log(context: dict):
    if not _env_bool("LUBAN_PROVISIONER_LOG_CONTEXT", True):
        return None

    mode = (os.getenv("LUBAN_PROVISIONER_LOG_CONTEXT_MODE", "summary") or "summary").strip().lower()
    mask_secrets = _env_bool("LUBAN_PROVISIONER_MASK_CONTEXT_SECRETS", True)

    if mode == "full":
        if mask_secrets:
            return mask_sensitive_context(context)
        return context

    return _summarize_context_for_log(context, mask_secrets=mask_secrets)


def mask_sensitive_context(value):
    if isinstance(value, dict):
        masked = {}
        for k, v in value.items():
            if _SENSITIVE_KEY_RE.search(str(k)):
                masked[k] = _mask_sensitive_value(v)
            else:
                masked[k] = mask_sensitive_context(v)
        return masked

    if isinstance(value, list):
        return [mask_sensitive_context(v) for v in value]

    if isinstance(value, tuple):
        return tuple(mask_sensitive_context(v) for v in value)

    return value


def _mask_sensitive_value(value):
    if value is None:
        return None

    if not isinstance(value, str):
        return "<masked>"

    if value == "":
        return ""

    if len(value) <= 4:
        return "*" * len(value)

    return f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "y", "on"}


def _summarize_context_for_log(context: dict, *, mask_secrets: bool):
    keys = sorted(str(k) for k in (context or {}).keys())

    safe_preview_keys = [
        "project_name",
        "app_name",
        "package_name",
        "repo_name",
        "env",
        "template_type",
    ]
    preview = {k: context.get(k) for k in safe_preview_keys if k in context}

    sensitive = {}
    for k, v in (context or {}).items():
        if _SENSITIVE_KEY_RE.search(str(k)):
            sensitive[k] = _mask_sensitive_value(v) if mask_secrets else v

    return {
        "keys": keys,
        "preview": preview,
        "sensitive": sensitive,
    }
