{{
  config(
    materialized="incremental",
    unique_key=["order_date", "customer_id"],
    tags=['daily']
  )
}}

select
  o.order_date,
  o.customer_id,
  count(*) as order_count,
  sum(o.order_amount) as total_amount
from {{ ref('orders') }} o

{% set w = luban_partition_window_date() %}
where o.order_date >= '{{ w["min_date"] }}'
  and o.order_date < '{{ w["max_date"] }}'

group by 1, 2
