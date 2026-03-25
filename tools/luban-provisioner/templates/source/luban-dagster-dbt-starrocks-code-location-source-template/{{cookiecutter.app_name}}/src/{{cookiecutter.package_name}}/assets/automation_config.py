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

# Tag-based daily partition support
# Models tagged with 'daily' in dbt will automatically be mapped to DailyPartitionsDefinition

