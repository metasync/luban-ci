{{
    config(
        materialized='incremental',
        unique_key='customer_id',
        incremental_strategy='merge',
        merge_update_columns=['first_name', 'last_name', 'updated_at']
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
