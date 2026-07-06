{{ config(
    materialized='incremental',
    unique_key=['ext_game_id']
) }}

with source_data as (
    SELECT * FROM {{ source('raw', 'games') }}
)

SELECT
    season,
    gameID          AS ext_game_id,
    awayTeamID      AS ext_away_team_id,
    homeTeamID      AS ext_home_team_id,
    startTimestamp  AS start_timestamp,
    startTimezone   AS start_timezone,
    streamingURL    AS streaming_url,
    week,
    location,
    awayScore       AS away_score,
    homeScore       AS home_score,
    status,
    updateTimestamp AS update_timestamp
FROM source_data

{% if is_incremental() %}
WHERE
    season >= CAST(EXTRACT(YEAR FROM CURRENT_DATE) AS INT)
{% endif %}
