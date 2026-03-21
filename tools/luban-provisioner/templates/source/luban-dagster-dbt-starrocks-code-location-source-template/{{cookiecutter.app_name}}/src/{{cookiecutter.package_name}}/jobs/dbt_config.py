from .lib.dbt_job_presets import dbt_cli_build_job, key_prefix_job, models_job


DBT_JOB_SPECS = [
    key_prefix_job(name="dbt_assets_job", prefix="dbt"),
    models_job(
        name="dbt_daily_facts_job",
        models=["fact_orders_daily", "fact_customer_orders_daily"],
        include_upstream=True,
    ),
    models_job(
        name="dbt_daily_customer_facts_job",
        models=["fact_customer_orders_daily"],
        include_upstream=True,
    ),
    dbt_cli_build_job(
        name="dbt_intraday_orders_daily_job",
        models=["fact_orders_daily"],
        include_upstream=True,
        vars={"daily_fact_lookback": 0},
    ),
    dbt_cli_build_job(
        name="dbt_finalize_orders_daily_job",
        models=["fact_orders_daily"],
        include_upstream=True,
        vars={"daily_fact_lookback": 1},
    ),
]

