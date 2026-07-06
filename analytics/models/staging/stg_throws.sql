{{ config(
    materialized='incremental',
    unique_key=['ext_game_id', 'point_id', 'possession_id', 'sequence_id']
) }}

with source_data as (
    SELECT * FROM {{ source('processed', 'ext_throws') }}
)

SELECT
    date             AS game_date,
    game_id          AS ext_game_id,
    season,
    month,
    point_id,
    possession_id,
    sequence_id,
    offense_team_id,
    defense_team_id,
    thrower_id       AS ext_thrower_id,
    receiver_id      AS ext_receiver_id,
    defender_id      AS ext_defender_id,
    is_completion,
    is_throwaway,
    is_drop,
    is_block,
    is_interception,
    is_assist,
    is_hockey_assist,
    is_huck,
    is_stall,
    is_callahan,
    start_x,
    start_y,
    end_x,
    end_y,
    yards_thrown,
    yards_received,
    throw_type
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
