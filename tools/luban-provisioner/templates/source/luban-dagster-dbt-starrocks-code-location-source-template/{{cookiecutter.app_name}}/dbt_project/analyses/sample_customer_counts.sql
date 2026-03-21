select
  count(*) as customer_count
from {{ ref('customers') }}

