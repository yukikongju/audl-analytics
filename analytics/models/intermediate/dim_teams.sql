{{ config(materialized='view') }}

with teams as (
    select
        season,
        ext_team_id,
        ext_division_id,
        division_name,
        city,
        name,
        full_name,
        abbrev
    from {{ ref('stg_teams') }}
),

game_team_seasons as (
    select distinct
        season,
        ext_team_id,
        team_season_id
    from {{ ref('stg_games') }}
), 

team_color as (
    select
        left(ext_game_id, 4) as season,
        abbrev,
        max(team_primary_hex) as primary_hex,
        max(team_secondary_hex) as secondary_hex,
        max(city) as city,
        max(team_name) as team_name,
    from {{ ref('stg_team_game_metadata') }}
    group by 1, 2
)


-- Resolve the as-played slug per team-season: prefer the current slug if the team
-- played under it that season, otherwise fall back to the renamed (old) slug via
-- team_slug_aliases (e.g. Colorado played as `summit` 2022-2024, `apex` from 2025).
select
    t.season,
    coalesce(cur.team_season_id, old.team_season_id) as team_season_id,
    case
        when cur.team_season_id is not null then t.ext_team_id  -- played under current slug
        when old.team_season_id is not null then a.old_slug     -- played under old slug
        else t.ext_team_id                                      -- no games; keep current
    end as ext_team_id,
    t.ext_division_id,
    t.division_name,
    t.abbrev,
    --  t.city,
    --  t.name,
    c.city, -- note: taking city and name from stg_team_game_metadata because stg_teams overrides with new team slug (when team is expansion team / has been renamed)
    c.team_name as name, 
    c.primary_hex,
    c.secondary_hex,
    --  t.full_name,
from teams t
left join team_color c 
    on t.abbrev = c.abbrev
        and t.season = c.season
left join {{ ref('team_slug_aliases') }} a
    on t.ext_team_id = a.current_slug
left join game_team_seasons cur
    on cur.season = t.season
   and cur.ext_team_id = t.ext_team_id
left join game_team_seasons old
    on old.season = t.season
   and old.ext_team_id = a.old_slug
