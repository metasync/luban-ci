{{
  config(
    enabled=var('enable_demo_ods', false),
    materialized='table',
    schema=var('ods_schema'),
    alias='customers',
    tags=['demo_ods']
  )
}}

{% set n = var('demo_ods_customers_count', 50) %}
{% set base_ts = var('demo_ods_base_ts', '') %}

{% if base_ts %}
  {% set ts_expr = "cast('" ~ base_ts ~ "' as datetime)" %}
{% else %}
  {% set ts_expr = "current_timestamp()" %}
{% endif %}

select *
from (
  {% for i in range(1, n + 1) %}
  select
    {{ i }} as customer_id,
    concat('First_', cast({{ i }} as varchar)) as first_name,
    concat('Last_', cast({{ i }} as varchar)) as last_name,
    {{ ts_expr }} as updated_at,
    {{ ts_expr }} as ods_created_at,
    {{ ts_expr }} as ods_updated_at
  {% if not loop.last %} union all {% endif %}
  {% endfor %}
) t
