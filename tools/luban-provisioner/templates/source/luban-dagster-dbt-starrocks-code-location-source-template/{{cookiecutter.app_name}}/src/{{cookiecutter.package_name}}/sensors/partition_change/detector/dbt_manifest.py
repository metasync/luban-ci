from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ....resources.dbt import get_dbt_project_dir


@dataclass(frozen=True)
class DbtModelNode:
    unique_id: str
    name: str
    tags: set[str]
    meta: dict[str, Any]


def _manifest_path() -> Path:
    return get_dbt_project_dir() / "target" / "manifest.json"


def load_manifest() -> dict[str, Any]:
    path = _manifest_path()
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def iter_model_nodes(manifest: dict[str, Any]) -> list[DbtModelNode]:
    nodes = manifest.get("nodes") or {}
    result: list[DbtModelNode] = []
    for unique_id, props in nodes.items():
        if not isinstance(props, dict):
            continue
        if props.get("resource_type") != "model":
            continue

        name = props.get("name")
        if not name:
            continue

        result.append(
            DbtModelNode(
                unique_id=unique_id,
                name=str(name),
                tags=set(props.get("tags") or []),
                meta=dict(props.get("meta") or {}),
            )
        )
    return result


def get_model_node_by_name(manifest: dict[str, Any], name: str) -> DbtModelNode:
    candidates = [n for n in iter_model_nodes(manifest) if n.name == name]
    if not candidates:
        raise ValueError(f"dbt model not found in manifest: {name}")
    if len(candidates) > 1:
        unique_ids = sorted([c.unique_id for c in candidates])
        raise ValueError(
            f"dbt model name is ambiguous in manifest: {name} (candidates: {unique_ids})"
        )
    return candidates[0]
