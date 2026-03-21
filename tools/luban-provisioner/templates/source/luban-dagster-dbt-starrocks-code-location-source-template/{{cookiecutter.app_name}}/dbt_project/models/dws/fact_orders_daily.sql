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

{% if is_incremental() %}
    -- Dagster partition variables
    where order_date >= '{{ var("min_date") }}'
      and order_date < '{{ var("max_date") }}'
{% endif %}

group by 1
