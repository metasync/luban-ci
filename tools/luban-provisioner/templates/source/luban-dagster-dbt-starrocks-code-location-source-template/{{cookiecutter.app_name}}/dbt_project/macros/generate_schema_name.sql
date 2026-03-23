{#
  Why override generate_schema_name?

  dbt's default behavior is to concatenate the target schema with a model's custom schema:
    <target.schema>_<custom_schema>

  In this template, StarRocks "schema" corresponds to a StarRocks database, and we intentionally
  set explicit full database names via STARROCKS_ODS_DB / STARROCKS_DWD_DB / STARROCKS_DWS_DB.

  If we keep dbt's default concatenation, dbt would try to build into invalid/doubled database
  names such as:
    test_app_dws_dev_test_app_ods_dev

  This override makes dbt use the configured schema/database verbatim.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
  {%- if custom_schema_name is not none -%}
    {{ custom_schema_name | trim }}
  {%- else -%}
    {%- set fqn_1 = node.fqn[1] if (node.fqn | length) > 1 else '' -%}
    {%- set original_file_path = node.original_file_path or '' -%}

    {%- if fqn_1 == 'dwd' -%}
      {{ env_var('STARROCKS_DWD_DB', 'dwd') }}
    {%- elif fqn_1 == 'dws' -%}
      {{ env_var('STARROCKS_DWS_DB', 'dws') }}
    {%- elif original_file_path.startswith('snapshots/') -%}
      {{ env_var('STARROCKS_DWS_DB', 'dws') }}
    {%- else -%}
      {{ target.schema }}
    {%- endif -%}
  {%- endif -%}
{%- endmacro %}
