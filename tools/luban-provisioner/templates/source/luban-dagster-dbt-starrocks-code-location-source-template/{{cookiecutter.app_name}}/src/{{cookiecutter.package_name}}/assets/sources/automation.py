from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ...resources.dbt import get_dbt_project_dir
from ..dbt.prepare import prepare_manifest_if_missing


def _manifest_path() -> Path:
    return get_dbt_project_dir() / "target" / "manifest.json"


def load_automation_observable_sources() -> list[dict[str, str]]:
    prepare_manifest_if_missing()
    with _manifest_path().open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    sources = manifest.get("sources") or {}
    specs: list[dict[str, str]] = []
    for props in sources.values():
        if not isinstance(props, dict):
            continue
        meta: dict[str, Any] = props.get("meta") or {}
        luban_meta: dict[str, Any] = meta.get("luban") or {}
        observe: dict[str, Any] = luban_meta.get("observe") or {}
        watermark_column = observe.get("watermark_column")
        if not watermark_column:
            continue
        source_name = props.get("source_name")
        table_name = props.get("name")
        if not source_name or not table_name:
            continue

        specs.append(
            {
                "source": str(source_name),
                "table": str(table_name),
                "watermark_column": str(watermark_column),
            }
        )

    return sorted(specs, key=lambda s: (s["source"], s["table"]))
