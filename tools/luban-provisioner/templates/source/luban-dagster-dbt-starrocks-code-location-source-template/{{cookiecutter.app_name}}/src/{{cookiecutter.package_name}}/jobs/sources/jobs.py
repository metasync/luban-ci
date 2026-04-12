from dagster import define_asset_job

from ...assets.sources.assets import observable_source_assets


observe_sources_job = define_asset_job(
    name="observe_sources_job",
    selection=observable_source_assets,
)

