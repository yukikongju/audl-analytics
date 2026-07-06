{{ config(materialized='view') }}

SELECT
    season,
    ext_team_id,
    ext_division_id,
    division_name,
    city,
    name,
    full_name,
    abbrev
FROM {{ ref('stg_teams') }}
