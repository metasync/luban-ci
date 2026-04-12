def models_job(
    *,
    name: str,
    models: list[str],
    key_prefix: str = "dbt",
    include_upstream: bool = False,
    partitions: str | None = None,
):
    if not name:
        raise ValueError("Job name must be non-empty")
    if not models:
        raise ValueError("Models list must be non-empty")

    keys = [[key_prefix, model] for model in models]
    return {
        "name": name,
        "selection": {
            "type": "asset_keys",
            "keys": keys,
            "upstream": include_upstream,
        },
        "partitions": partitions,
    }


def dbt_cli_build_job(
    *,
    name: str,
    models: list[str],
    vars: dict | None = None,
    include_upstream: bool = False,
    partitions: str = "daily",
):
    if not name:
        raise ValueError("Job name must be non-empty")
    if not models:
        raise ValueError("Models list must be non-empty")

    prefix = "+" if include_upstream else ""
    select_str = " ".join([f"{prefix}{model}" for model in models])

    return {
        "type": "dbt_cli",
        "name": name,
        "command": "build",
        "select": select_str,
        "vars": vars or {},
        "partitions": partitions,
    }
