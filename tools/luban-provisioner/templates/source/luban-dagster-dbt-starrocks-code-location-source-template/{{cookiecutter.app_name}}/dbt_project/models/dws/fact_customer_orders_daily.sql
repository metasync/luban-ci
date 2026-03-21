{{
  config(
    tags=["daily"],
    materialized="incremental",
    unique_key=["order_date", "customer_id"],
  )
}}

select
  o.order_date,
  o.customer_id,
  count(*) as order_count,
  sum(o.order_amount) as total_amount
from {{ ref('orders') }} o

{% if is_incremental() %}
    -- Dagster partition variables
    where o.order_date >= '{{ var("min_date") }}'
      and o.order_date < '{{ var("max_date") }}'
{% endif %}

group by 1, 2
