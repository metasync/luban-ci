from __future__ import annotations

from .automation import load_automation_observable_sources
from ..dbt.assets import dbt_assets
from .factory import build_observable_source_assets


observable_source_assets = build_observable_source_assets(
    dbt_assets=dbt_assets,
    source_specs=load_automation_observable_sources(),
)

