{{ config(
    materialized='incremental',
    unique_key=['year', 'ext_team_id']
) }}

with source_data as (
    SELECT * FROM {{ source('raw', 'teams') }}
)

SELECT
    season,
    teamID              AS ext_team_id,
    division.divisionID AS ext_division_id,
    division.name       AS division_name,
    city,
    name,
    fullName            AS full_name,
    abbrev,
    year,
    wins,
    losses,
    ties,
    standing
FROM source_data

{% if is_incremental() %}
WHERE
    season >= CAST(EXTRACT(YEAR FROM CURRENT_DATE) AS INT)
{% endif %}
