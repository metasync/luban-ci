{{
    config(
        materialized='incremental',
        unique_key='order_id',
        incremental_strategy='merge',
        merge_update_columns=['customer_id', 'order_amount', 'order_datetime', 'order_date', 'updated_at'],
        event_time='order_datetime'
    )
}}

select
  order_id,
  customer_id,
  order_amount,
  order_datetime,
  cast(order_datetime as date) as order_date,
  updated_at
from {{ source('ods', 'orders') }}

{% if is_incremental() %}
    -- Dagster partition variables
    where order_datetime >= '{{ var("min_datetime") }}'
      and order_datetime < '{{ var("max_datetime") }}'
{% endif %}
