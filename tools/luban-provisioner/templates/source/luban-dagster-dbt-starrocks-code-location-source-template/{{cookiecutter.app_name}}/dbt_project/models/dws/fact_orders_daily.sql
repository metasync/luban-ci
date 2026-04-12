{{
  config(
    materialized="incremental",
    unique_key="order_date",
    tags=['daily']
  )
}}

select
  order_date,
  count(*) as order_count,
  sum(order_amount) as total_amount
from {{ ref('orders') }}

{% set w = luban_partition_window_date() %}
where order_date >= '{{ w["min_date"] }}'
  and order_date < '{{ w["max_date"] }}'

group by 1
