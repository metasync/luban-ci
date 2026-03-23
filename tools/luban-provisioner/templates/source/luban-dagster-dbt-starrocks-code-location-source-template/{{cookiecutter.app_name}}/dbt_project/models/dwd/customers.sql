{{
    config(
        materialized='incremental',
        incremental_strategy='default',
        table_type='PRIMARY',
        keys=['customer_id']
    )
}}

select
  customer_id,
  first_name,
  last_name,
  updated_at
from {{ source('ods', 'customers') }}

{% if is_incremental() %}
  where updated_at > (select max(updated_at) from {{ this }})
{% endif %}
