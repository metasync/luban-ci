import os
import pytest
from dagster import load_assets_from_modules

# Ensure Dagster doesn't try to actually connect to dbt or StarRocks during simple definition tests
os.environ["DAGSTER_DBT_PARSE_PROJECT_ON_LOAD"] = "0"
os.environ["STARROCKS_HOST"] = "mock_host"
os.environ["STARROCKS_PORT"] = "9030"
os.environ["STARROCKS_USER"] = "mock_user"
os.environ["STARROCKS_PASSWORD"] = "mock_pass"

from {{cookiecutter.package_name}} import defs


def test_definitions_load():
    """
    Tests that the Dagster Definitions object loads successfully without syntax errors
    or missing dependencies.
    """
    assert defs is not None
    
    # Verify basic structure
    assert len(defs.assets) > 0
    assert len(defs.jobs) > 0
    assert len(defs.schedules) > 0
    assert "starrocks" in defs.resources

def test_dbt_assets_present():
    """
    Tests that dbt assets are successfully loaded into the definitions.
    """
    asset_keys = [asset.key.to_user_string() for asset in defs.get_all_asset_specs()]
    
    # We expect to see some standard dbt assets based on our dbt project
    # This might need adjustment if dbt models are renamed
    assert any("dbt" in key for key in asset_keys)
