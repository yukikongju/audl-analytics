{{ config(materialized='view') }}

-- Franchise renames derived from data (no manual upkeep on backfill / new seasons):
-- in the rename season the games feed records the team under BOTH slugs with the
-- SAME team_season_id. The slug present in stg_teams is the current one; the other
-- is the old one.
-- NOTE: DEPRECATED
with game_team_seasons as (
    select distinct ext_team_id, team_season_id
    from {{ ref('stg_games') }}
),

multi_slug as (
    select team_season_id
    from game_team_seasons
    group by team_season_id
    having count(distinct ext_team_id) > 1
),

pairs as (
    select g.team_season_id, g.ext_team_id
    from game_team_seasons g
    join multi_slug m using (team_season_id)
),

current_slugs as (
    select distinct ext_team_id from {{ ref('stg_teams') }}
)

select distinct
    o.ext_team_id as old_slug,
    c.ext_team_id as current_slug
from pairs o
join pairs c
    on o.team_season_id = c.team_season_id
   and o.ext_team_id <> c.ext_team_id
where c.ext_team_id in (select ext_team_id from current_slugs)
  and o.ext_team_id not in (select ext_team_id from current_slugs)
