from .dbt.assets import dbt_assets
from .sources.assets import observable_source_assets

assets = (dbt_assets if isinstance(dbt_assets, list) else [dbt_assets]) + observable_source_assets
