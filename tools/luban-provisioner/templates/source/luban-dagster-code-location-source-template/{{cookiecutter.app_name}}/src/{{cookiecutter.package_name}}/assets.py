from dagster import asset

@asset
def simple_asset():
    """A simple asset that returns a greeting."""
    return "Hello from {{cookiecutter.app_name}}!"
