from __future__ import annotations

from .automation_config import AUTOMATION_OBSERVABLE_SOURCES
from .dbt import dbt_assets
from .lib.observable_sources_factory import build_observable_source_assets


observable_source_assets = build_observable_source_assets(
    dbt_assets=dbt_assets,
    source_specs=AUTOMATION_OBSERVABLE_SOURCES,
)

