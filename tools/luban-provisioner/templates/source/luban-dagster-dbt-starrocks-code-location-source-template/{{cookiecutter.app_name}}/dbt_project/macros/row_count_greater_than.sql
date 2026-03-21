{% test row_count_greater_than(model, min_value) %}

select
  count(*) as row_count
from {{ model }}
having count(*) <= {{ min_value }}

{% endtest %}

