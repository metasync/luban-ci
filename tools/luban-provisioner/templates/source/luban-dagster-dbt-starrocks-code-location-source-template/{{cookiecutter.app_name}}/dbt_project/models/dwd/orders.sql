{{
    config(
        materialized='incremental',
        incremental_strategy='dynamic_overwrite',
        partition_by=['order_date']
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
