{% macro luban_ods_db() -%}
  {{ env_var('STARROCKS_ODS_DB', 'ods') }}
{%- endmacro %}

{% macro luban_dwd_db() -%}
  {{ env_var('STARROCKS_DWD_DB', 'dwd') }}
{%- endmacro %}

{% macro luban_dws_db() -%}
  {{ env_var('STARROCKS_DWS_DB', 'dws') }}
{%- endmacro %}
