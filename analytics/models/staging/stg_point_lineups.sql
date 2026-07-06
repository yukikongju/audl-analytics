{{ config(
    materialized='incremental',
    unique_key=['ext_game_id', 'point_id', 'stint_id']
) }}

with source_data as (
    SELECT * FROM {{ source('processed', 'ext_point_lineups') }}
)

SELECT
    season,
    month,
    game_id          AS ext_game_id,
    point_id,
    stint_id,
    team_id,
    team_score,
    opponent_score,
    lineup,
    line_type,
    is_stint_scoring,
    stint_start_time,
    stint_end_time,
    seconds_played
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
