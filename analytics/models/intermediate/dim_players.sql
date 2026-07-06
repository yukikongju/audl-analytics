{{ config(materialized='view') }}

SELECT
    team_year,
    ext_team_id,
    ext_player_id,
    first_name,
    last_name,
    jersey_number,
    season
FROM {{ ref('stg_players') }}
