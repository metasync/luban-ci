{{
  config(
    enabled=var('enable_demo_ods', false),
    materialized='table',
    schema=var('ods_schema'),
    alias='orders',
    tags=['demo_ods']
  )
}}

{% set customers = var('demo_ods_customers_count', 50) %}
{% set per_customer = var('demo_ods_orders_per_customer', 3) %}
{% set days = var('demo_ods_days', 7) %}
{% set base_ts = var('demo_ods_base_ts', '') %}

{% if base_ts %}
  {% set base_expr = "cast('" ~ base_ts ~ "' as datetime)" %}
{% else %}
  {% set base_expr = "current_timestamp()" %}
{% endif %}

{% set anchor_expr = "date_trunc('hour', " ~ base_expr ~ ")" %}
{% set total_hours = days * 24 %}
{% set total_orders = customers * per_customer %}

select *
from (
  {% for seq in range(0, total_orders) %}
    {% set c = (seq // per_customer) + 1 %}
    {% set k = (seq % per_customer) + 1 %}
    {% set hour_offset = seq % total_hours %}
    select
      ({{ c }} * 1000000 + {{ k }}) as order_id,
      {{ c }} as customer_id,
      ({{ k }} * 10 + ({{ c }} % 10)) as order_amount,
      hours_sub({{ anchor_expr }}, {{ hour_offset }}) as order_datetime,
      {{ base_expr }} as updated_at,
      {{ base_expr }} as ods_created_at,
      {{ base_expr }} as ods_updated_at
    {% if not loop.last %} union all {% endif %}
  {% endfor %}
) t
