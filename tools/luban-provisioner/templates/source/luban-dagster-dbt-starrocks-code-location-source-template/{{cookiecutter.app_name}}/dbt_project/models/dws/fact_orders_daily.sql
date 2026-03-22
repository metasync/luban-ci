{{
  config(
    tags=["daily"],
    materialized="incremental",
    unique_key="order_date",
  )
}}

select
  order_date,
  count(*) as order_count,
  sum(order_amount) as total_amount
from {{ ref('orders') }}

{% set w = luban_partition_window_date() %}
where order_date >= cast('{{ w["min_date"] }}' as date)
  and order_date < cast('{{ w["max_date"] }}' as date)

group by 1
