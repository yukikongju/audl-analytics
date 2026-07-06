{{ config(
    materialized='incremental',
    unique_key=['ext_game_id', 'point_id', 'possession_id', 'sequence_id']
) }}

with source_data as (
    SELECT * FROM {{ source('processed', 'ext_blocks') }}
)

SELECT
    season,
    month,
    game_id             AS ext_game_id,
    sequence_id,
    possession_id,
    point_id,
    defender_id         AS ext_defender_id,
    is_callahan,
    defense_team_id,
    defense_ext_team_id AS ext_defense_team_id
FROM source_data

{% if is_incremental() %}
WHERE
    season >= CAST(EXTRACT(YEAR FROM CURRENT_DATE) AS INT)
    AND NOT EXISTS (
        SELECT 1
        FROM {{ this }} target_table
        WHERE target_table.ext_game_id = source_data.game_id
    )
{% endif %}
