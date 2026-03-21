AUTOMATION_OBSERVABLE_SOURCES = [
    {
        "source": "ods",
        "table": "customers",
        "watermark_column": "ods_updated_at",
    },
    {
        "source": "ods",
        "table": "orders",
        "watermark_column": "ods_updated_at",
    },
]

# List of dbt model names that should be mapped to the Dagster DailyPartitionsDefinition.
# Models tagged with 'daily' in dbt will automatically be included and do not need to be listed here.
DAGSTER_DAILY_PARTITIONED_MODELS = [
    "orders",
]

