{{
  config(
    materialized="incremental",
    unique_key=["order_date", "customer_id"],
    tags=["dynamic__fact_customer_orders_dynamic_daily"]
  )
}}

{% set pk = var("partition_key", none) %}

select
  o.order_date,
  o.customer_id,
  c.first_name,
  c.last_name,
  count(*) as order_count,
  sum(o.order_amount) as total_amount
from {{ ref('orders') }} o
left join {{ ref('customers') }} c
  on o.customer_id = c.customer_id

{% if pk is not none %}
where o.order_date = '{{ pk }}'
{% elif is_incremental() %}
where o.order_date >= (select max(order_date) from {{ this }})
{% endif %}

group by 1, 2, 3, 4