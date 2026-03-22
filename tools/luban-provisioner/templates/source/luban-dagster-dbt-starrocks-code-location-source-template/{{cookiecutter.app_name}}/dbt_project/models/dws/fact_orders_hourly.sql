{{
  config(
    tags=["hourly"],
    materialized="incremental",
    unique_key="order_hour",
  )
}}

select
  date_trunc('hour', order_datetime) as order_hour,
  count(*) as order_count,
  sum(order_amount) as total_amount
from {{ ref('orders') }}

{% set w = luban_partition_window_datetime() %}
where order_datetime >= '{{ w["min_datetime"] }}'
  and order_datetime < '{{ w["max_datetime"] }}'

group by 1
