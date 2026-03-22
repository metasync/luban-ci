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

{% set w = luban_partition_window_datetime() %}
where order_datetime >= '{{ w["min_datetime"] }}'
  and order_datetime < '{{ w["max_datetime"] }}'
