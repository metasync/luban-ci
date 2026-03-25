{{
  config(
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
  -- Incremental processing: only process new/updated data
  where o.order_date >= (select max(order_date) from {{ this }})
{% endif %}

group by 1, 2
