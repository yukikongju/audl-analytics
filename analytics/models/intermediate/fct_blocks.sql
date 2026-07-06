{{ config(materialized='view') }}

SELECT
    season,
    month,
    {{ parse_game_date('ext_game_id') }} AS game_date,
    ext_game_id,
    sequence_id,
    possession_id,
    point_id,
    ext_defender_id,
    is_callahan
FROM {{ ref('stg_blocks') }}
