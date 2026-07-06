{{ config(
    materialized='incremental',
    unique_key=['game_id']
) }}

with source_data as (
    SELECT * FROM {{ source('processed', 'ext_games') }}
)

SELECT
    game_ext_id        AS ext_game_id,
    month,
    season,
    id,
    gameId             AS game_id,
    startOnOffense     AS start_on_offense,
    completionsNumer   AS completions_numer,
    completionsDenom   AS completions_denom,
    hucksNumer         AS hucks_numer,
    hucksDenom         AS hucks_denom,
    blocks,
    turnovers,
    oLineScores        AS o_line_scores,
    oLinePoints        AS o_line_points,
    oLinePossessions   AS o_line_possessions,
    dLineScores        AS d_line_scores,
    dLinePoints        AS d_line_points,
    dLinePossessions   AS d_line_possessions,
    redZoneScores      AS red_zone_scores,
    redZonePossessions AS red_zone_possessions,
    isHome             AS is_home,
    rosterIds          AS roster_ids,
    score,
    score_times,
    teamSeasonId       AS team_season_id,
    ext_team_id,
    statusId           AS status_id,
    source,
    updateMoment       AS update_moment
FROM source_data

{% if is_incremental() %}
WHERE
    season >= CAST(EXTRACT(YEAR FROM CURRENT_DATE) AS INT)
    --  AND game_id NOT IN (
        --  SELECT DISTINCT game_id
        --  FROM {{ this }}
    --  )
{% endif %}
