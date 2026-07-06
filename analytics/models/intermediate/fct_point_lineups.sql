{{ config(materialized='view') }}

SELECT
    season,
    month,
    {{ parse_game_date('ext_game_id') }} AS game_date,
    ext_game_id,
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
FROM {{ ref('stg_point_lineups') }}
