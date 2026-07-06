{{ config(
    materialized='incremental',
    unique_key=['ext_game_id', 'point_id']
) }}

with source_data as (
    SELECT * FROM {{ source('processed', 'ext_pulls') }}
)

SELECT
    season,
    month,
    game_id          AS ext_game_id,
    point_id,
    pull_sequence,
    pulling_team_id,
    puller_id        AS ext_puller_id,
    hangtime_seconds,
    is_out_of_bounds,
    end_x,
    end_y
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
