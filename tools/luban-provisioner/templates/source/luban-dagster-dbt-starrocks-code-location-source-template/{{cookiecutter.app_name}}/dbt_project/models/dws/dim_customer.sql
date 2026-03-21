{{
  config(
    tags=["dim"],
    materialized="incremental",
    incremental_strategy="merge",
    unique_key="customer_id",
    merge_update_columns=['first_name', 'last_name', 'updated_at']
  )
}}

select
  customer_id,
  first_name,
  last_name,
  updated_at
from {{ ref('customers') }}

{% if is_incremental() %}
  where updated_at > (select max(updated_at) from {{ this }})
{% endif %}

