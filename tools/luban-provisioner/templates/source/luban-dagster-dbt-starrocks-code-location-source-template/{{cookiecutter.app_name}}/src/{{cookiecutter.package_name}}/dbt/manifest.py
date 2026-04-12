from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from ..assets.dbt.prepare import prepare_manifest_if_missing
from ..resources.dbt import get_dbt_project_dir


@dataclass(frozen=True)
class DbtModel:
    name: str
    fqn: list[str]
    tags: set[str]
    meta: dict[str, Any]


def _manifest_path() -> Path:
    return get_dbt_project_dir() / "target" / "manifest.json"


@lru_cache(maxsize=1)
def load_manifest() -> dict[str, Any]:
    prepare_manifest_if_missing()
    path = _manifest_path()
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def iter_models(manifest: dict[str, Any]) -> list[DbtModel]:
    nodes = manifest.get("nodes") or {}
    result: list[DbtModel] = []
    for props in nodes.values():
        if not isinstance(props, dict):
            continue
        if props.get("resource_type") != "model":
            continue

        name = props.get("name")
        if not name:
            continue

        result.append(
            DbtModel(
                name=str(name),
                fqn=list(props.get("fqn") or []),
                tags=set(props.get("tags") or []),
                meta=dict(props.get("meta") or {}),
            )
        )
    return result


def first_tag_value(tags: set[str], *, prefix: str) -> str | None:
    for tag in tags:
        if not isinstance(tag, str):
            continue
        if tag.startswith(prefix):
            return tag[len(prefix) :]
    return None


def get_luban_meta(meta: dict[str, Any]) -> dict[str, Any]:
    luban = meta.get("luban")
    return luban if isinstance(luban, dict) else {}
