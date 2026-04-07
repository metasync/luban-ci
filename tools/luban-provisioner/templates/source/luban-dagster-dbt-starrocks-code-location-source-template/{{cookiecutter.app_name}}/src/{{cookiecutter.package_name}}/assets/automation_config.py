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

DYNAMIC_TAG_PREFIX = "dynamic__"
DYNAMIC_PARTITION_PIPELINES = [
    {
        "name": "fact_customer_orders_dynamic_daily",
        "dbt_tag": f"{DYNAMIC_TAG_PREFIX}fact_customer_orders_dynamic_daily",
        "partitions_def_name": f"{DYNAMIC_TAG_PREFIX}fact_customer_orders_dynamic_daily__partitions",
        "job_name": f"{DYNAMIC_TAG_PREFIX}fact_customer_orders_dynamic_daily__job",
        "sensor_name": f"{DYNAMIC_TAG_PREFIX}fact_customer_orders_dynamic_daily__sensor",
        "sensor_default_status": "STOPPED",
        "dispatch_daily_utc_hour": 8,
        "dispatch_slot_seconds": None,
        "max_keys_per_tick": 5000,
        "sources": [
            {
                "source_id": "dwd_orders",
                "mode": "table_keys",
                "db_env_var": "STARROCKS_DWD_DB",
                "db_default": "dwd",
                "table": "orders",
                "updated_at_column": "updated_at",
                "key_column": "order_date",
            },
            {
                "source_id": "dwd_customers_lookback",
                "mode": "lookback",
                "db_env_var": "STARROCKS_DWD_DB",
                "db_default": "dwd",
                "table": "customers",
                "updated_at_column": "updated_at",
                "lookback_days": 7,
            },
        ],
    },
]

# Tag-based daily partition support
# Models tagged with 'daily' in dbt will automatically be mapped to DailyPartitionsDefinition

