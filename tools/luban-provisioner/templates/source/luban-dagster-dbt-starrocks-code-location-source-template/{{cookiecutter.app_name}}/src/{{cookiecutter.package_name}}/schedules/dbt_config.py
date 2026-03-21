from .lib.dbt_schedule_presets import daily_at, hourly_at


DBT_SCHEDULE_SPECS = [
    daily_at(name="daily_facts_schedule", job_name="dbt_daily_customer_facts_job", hour=1, minute=0, enabled=True),
    daily_at(
        name="finalize_orders_daily_schedule",
        job_name="dbt_finalize_orders_daily_job",
        hour=1,
        minute=5,
        enabled=True,
    ),
    hourly_at(
        name="intraday_orders_daily_schedule",
        job_name="dbt_intraday_orders_daily_job",
        minute=0,
        enabled=False,
    ),
]

