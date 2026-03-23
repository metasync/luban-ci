{% macro sr_ods_db() -%}
  {{ env_var('STARROCKS_ODS_DB', 'ods') }}
{%- endmacro %}

{% macro sr_dwd_db() -%}
  {{ env_var('STARROCKS_DWD_DB', 'dwd') }}
{%- endmacro %}

{% macro sr_dws_db() -%}
  {{ env_var('STARROCKS_DWS_DB', 'dws') }}
{%- endmacro %}
