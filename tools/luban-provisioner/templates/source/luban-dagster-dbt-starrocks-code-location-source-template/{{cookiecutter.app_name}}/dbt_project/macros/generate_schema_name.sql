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
    {{ starrocks_layer_schema(node) }}
  {%- endif -%}
{%- endmacro %}
