{{ config(materialized='incremental', unique_key=['ext_game_id', 'ext_thrower_id', 'ext_receiver_id']) }}

-- One row per thrower -> receiver connection per game, with throw-type distribution.
-- Only throws with a known receiver are counted (turnovers with no target are excluded).
with throws as (
    select
        season,
        ext_game_id,
        offense_team_id,
        defense_team_id,
        ext_thrower_id,
        ext_receiver_id,
        sum(case when throw_type = 'huck' and is_completion then 1 else 0 end) as hucks_completed,
        sum(case when throw_type = 'huck' then 1 else 0 end) as hucks_attempted,
        sum(case when throw_type = 'pass' and is_completion then 1 else 0 end) as pass_completed,
        sum(case when throw_type = 'pass' then 1 else 0 end) as pass_attempted,
        sum(case when throw_type = 'dump' and is_completion then 1 else 0 end) as dump_completed,
        sum(case when throw_type = 'dump' then 1 else 0 end) as dump_attempted,
        sum(case when throw_type = 'swing' and is_completion then 1 else 0 end) as swing_completed,
        sum(case when throw_type = 'swing' then 1 else 0 end) as swing_attempted
    from {{ ref('fct_throws') }}
    where ext_receiver_id is not null
    {% if is_incremental() %}
      and season >= cast(extract(year from current_date) as int)
      and ext_game_id not in (select ext_game_id from {{ this }})
    {% endif %}
    group by 1, 2, 3, 4, 5, 6
)

select
    t.season,
    t.ext_game_id,
    t.offense_team_id,
    ot.ext_team_id as offense_ext_team_id,
    t.defense_team_id,
    dt.ext_team_id as defense_ext_team_id,
    t.ext_thrower_id,
    t.ext_receiver_id,
    t.hucks_completed,
    t.hucks_attempted,
    t.pass_completed,
    t.pass_attempted,
    t.dump_completed,
    t.dump_attempted,
    t.swing_completed,
    t.swing_attempted
from throws t
left join {{ ref('dim_teams') }} ot on ot.season = t.season and ot.team_season_id = t.offense_team_id
left join {{ ref('dim_teams') }} dt on dt.season = t.season and dt.team_season_id = t.defense_team_id
