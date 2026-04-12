{{
    config(
        materialized='incremental',
        incremental_strategy='default',
        table_type='PRIMARY',
        keys=['order_id'],
        tags=[
            'daily',
            'asset_job'
        ],
        meta={
            'luban': {
                'asset_schedule': {
                    'name': 'orders_anchor_daily_schedule',
                    'type': 'daily_at',
                    'hour': 1,
                    'minute': 0,
                    'lookback_days': 0,
                    'enabled': True
                },
                'partition_change': {
                    'detector': {
                        'enabled': True,
                        'lookback_days': 7,
                        'offset_days': 1,
                        'detect_source': {
                            'source': 'ods',
                            'table': 'orders'
                        },
                        'partition_date_expr': 'order_datetime',
                        'updated_at_expr': 'updated_at'
                    },
                    'propagate': {
                        'enabled': True,
                        'name': 'facts_from_orders_partitions_sensor',
                        'minimum_interval_seconds': 30,
                        'targets': [
                            {
                                'job_name': 'daily_facts_job'
                            }
                        ]
                    }
                }
            }
        }
    )
}}

select
  order_id,
  customer_id,
  order_amount,
  order_datetime,
  cast(order_datetime as date) as order_date,
  updated_at
from {{ source('ods', 'orders') }}

{% set w = luban_partition_window_datetime() %}
where order_datetime >= '{{ w["min_datetime"] }}'
  and order_datetime < '{{ w["max_datetime"] }}'
