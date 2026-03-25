from .lib.dbt_job_presets import dbt_cli_build_job, key_prefix_job, models_job


DBT_JOB_SPECS = [
    dbt_cli_build_job(
        name="dbt_daily_facts_job",
        models=["fact_orders_daily", "fact_customer_orders_daily"],
        include_upstream=False,
        partitions="daily",
    ),
    dbt_cli_build_job(
        name="dbt_daily_customer_facts_job",
        models=["fact_customer_orders_daily"],
        include_upstream=False,
        partitions="daily",
    ),
    dbt_cli_build_job(
        name="dbt_orders_daily_job",
        models=["fact_orders_daily"],
        include_upstream=False,
    ),
]
