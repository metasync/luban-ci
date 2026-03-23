{% macro starrocks_layer_schema(node) -%}
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
{%- endmacro %}
