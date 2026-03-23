{% snapshot customers_snapshot %}

{{
  config(
    target_schema="{{ sr_dws_db() }}",
    unique_key='customer_id',
    strategy='check',
    check_cols=['first_name', 'last_name'],
  )
}}

select
  customer_id,
  first_name,
  last_name
from {{ ref('customers') }}

{% endsnapshot %}
