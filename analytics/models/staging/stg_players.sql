{{ config(
    materialized='incremental',
    unique_key=['team_year', 'ext_team_id', 'ext_player_id']
) }}

with source_data as (
    SELECT * FROM {{ source('raw', 'players') }}
),

unnested as (
    SELECT
        playerID,
        firstName,
        lastName,
        season,
        UNNEST(teams) AS team
    FROM source_data
)

SELECT
    team.year         AS team_year,
    team.teamID       AS ext_team_id,
    playerID          AS ext_player_id,
    firstName         AS first_name,
    lastName          AS last_name,
    team.jerseyNumber AS jersey_number,
    team.active       AS active,
    season
FROM unnested

{% if is_incremental() %}
WHERE
    season >= CAST(EXTRACT(YEAR FROM CURRENT_DATE) AS INT)
{% endif %}
