{{ config(materialized='view') }}

SELECT
    season,
    month,
    {{ parse_game_date('ext_game_id') }} AS game_date,
    ext_game_id,
    point_id,
    pull_sequence,
    pulling_team_id,
    ext_puller_id,
    hangtime_seconds,
    is_out_of_bounds,
    end_x,
    end_y
FROM {{ ref('stg_pulls') }}
