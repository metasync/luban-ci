{% macro starrocks__drop_relation(relation) -%}
  {% call statement('drop_relation', auto_begin=False) -%}
    drop {{ relation.type }} if exists {{ relation }} force
  {%- endcall %}
{% endmacro %}

{% macro starrocks__make_temp_relation(base_relation, suffix) %}
    {%- set tmp_identifier = base_relation.identifier ~ suffix ~ '__dbt_tmp_' ~ invocation_id.replace('-', '') -%}
    {%- do return(base_relation.incorporate(
                                  path={
                                    "identifier": tmp_identifier,
                                    "schema": base_relation.schema,
                                    "database": base_relation.database
                                  }
    )) -%}
{% endmacro %}

