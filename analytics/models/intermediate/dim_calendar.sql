{{ config(materialized='view') }}

SELECT
    season,
    {{ parse_game_date('ext_game_id') }} AS game_date,
    ext_game_id,
    ext_away_team_id,
    ext_home_team_id,
    start_timestamp,
    start_timezone,
    streaming_url,
    week,
    location
FROM {{ ref('stg_calendar') }}
