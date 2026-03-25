from .lib.dbt_schedule_presets import daily_at, hourly_at


DBT_SCHEDULE_SPECS = [
    daily_at(
        name="daily_facts_schedule",
        job_name="dbt_daily_customer_facts_job",
        lookback_days=0,
        hour=1,
        minute=0,
        enabled=True,
    ),
    daily_at(
        name="orders_daily_schedule",
        job_name="dbt_orders_daily_job",
        lookback_days=1,
        hour=1,
        minute=0,
        enabled=True,
    ),
]
