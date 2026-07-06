{#-
    Extract the game date from an ext_game_id.
    ext_game_id is always date-prefixed, e.g. "2026-05-10-MTL-PIT" -> 2026-05-10.
-#}
{% macro parse_game_date(ext_game_id) -%}
    CAST(SUBSTRING({{ ext_game_id }}, 1, 10) AS DATE)
{%- endmacro %}
