{{
  config(
    materialized="incremental",
    unique_key="order_hour",
  )
}}

select
  date_trunc('hour', order_datetime) as order_hour,
  count(*) as order_count,
  sum(order_amount) as total_amount
from {{ ref('orders') }}

{% if is_incremental() %}
  -- Incremental processing: only process new/updated data
  where order_datetime >= (select max(order_hour) from {{ this }})
{% endif %}

group by 1
