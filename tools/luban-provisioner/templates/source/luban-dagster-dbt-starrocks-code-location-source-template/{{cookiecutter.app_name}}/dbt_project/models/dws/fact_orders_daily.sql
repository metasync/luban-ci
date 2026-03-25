{{
  config(
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
  -- Incremental processing: only process new/updated data
  where order_date >= (select max(order_date) from {{ this }})
{% endif %}

group by 1
