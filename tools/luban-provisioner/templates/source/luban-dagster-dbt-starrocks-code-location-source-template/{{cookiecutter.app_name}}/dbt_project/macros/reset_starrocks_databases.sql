{% macro reset_starrocks_databases(layers=[]) -%}
  {%- if layers is string -%}
    {%- set layers = [layers] -%}
  {%- endif -%}

  {%- for layer in layers -%}
    {%- if layer == 'ods' -%}
      {%- set db = env_var('STARROCKS_ODS_DB', 'ods') -%}
    {%- elif layer == 'dwd' -%}
      {%- set db = env_var('STARROCKS_DWD_DB', 'dwd') -%}
    {%- elif layer == 'dws' -%}
      {%- set db = env_var('STARROCKS_DWS_DB', 'dws') -%}
    {%- else -%}
      {% do exceptions.raise_compiler_error("Unsupported layer: " ~ layer) %}
    {%- endif -%}

    {%- if not modules.re.match('^[A-Za-z0-9_]+$', db) -%}
      {% do exceptions.raise_compiler_error("Unsafe database name: " ~ db) %}
    {%- endif -%}

    {% do log("Resetting StarRocks database: " ~ db, info=True) %}
    {% do run_query('drop database if exists `' ~ db ~ '`') %}
    {% do run_query('create database if not exists `' ~ db ~ '`') %}
  {%- endfor -%}
{%- endmacro %}
