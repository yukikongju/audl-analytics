{{ config(materialized='view') }}

with players as (
    -- stg_players uses the CURRENT franchise slug; keep it for the join
    select
        team_year,
        --  ext_team_id as current_slug,
        ext_team_id,
        ext_player_id,
        first_name,
        last_name,
        jersey_number
    from {{ ref('stg_players') }}
)

-- Join dim_teams to inherit team_season_id and the AS-PLAYED slug. dim_teams may
-- carry either the current slug (recent seasons) or the old slug (pre-rename), so
-- match on either; exactly one dim_teams row exists per franchise-season.
select distinct
    p.team_year as season,
    --  dt.team_season_id,
    -- coalesce(dt.ext_team_id, p.current_slug) as ext_team_id,
    p.ext_team_id,
    p.ext_player_id,
    p.first_name,
    p.last_name,
    p.jersey_number
from players p
--  left join {{ ref('team_slug_aliases') }} a
    --  on p.current_slug = a.current_slug
left join {{ ref('dim_teams') }} dt
    on dt.season = p.team_year
    and dt.ext_team_id = p.ext_team_id
   --  and (dt.ext_team_id = p.current_slug or dt.ext_team_id = a.old_slug)
