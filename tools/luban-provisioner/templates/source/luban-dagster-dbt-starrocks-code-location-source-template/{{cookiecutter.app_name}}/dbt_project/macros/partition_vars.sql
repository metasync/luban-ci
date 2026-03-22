{% macro luban_partition_window_date() %}
  {% set min_date = var('min_date', none) %}
  {% set max_date = var('max_date', none) %}
  {% if execute and (min_date is none or max_date is none) %}
    {{ exceptions.raise_compiler_error("Missing required dbt vars 'min_date'/'max_date'. Run this model via Dagster partitioned execution (or pass --vars with a partition window).") }}
  {% endif %}
  {{ return({"min_date": min_date or "1970-01-01", "max_date": max_date or "1970-01-02"}) }}
{% endmacro %}


{% macro luban_partition_window_datetime() %}
  {% set min_datetime = var('min_datetime', none) %}
  {% set max_datetime = var('max_datetime', none) %}
  {% if execute and (min_datetime is none or max_datetime is none) %}
    {{ exceptions.raise_compiler_error("Missing required dbt vars 'min_datetime'/'max_datetime'. Run this model via Dagster partitioned execution (or pass --vars with a partition window).") }}
  {% endif %}
  {{ return({"min_datetime": min_datetime or "1970-01-01 00:00:00", "max_datetime": max_datetime or "1970-01-02 00:00:00"}) }}
{% endmacro %}
