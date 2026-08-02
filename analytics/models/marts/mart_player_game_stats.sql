{{ config(materialized='incremental', unique_key=['ext_game_id', 'team_id', 'ext_player_id']) }}

with lineups as (
    select
        season,
        ext_game_id,
        point_id,
        team_id,
        line_type,
        is_stint_scoring,
        seconds_played,
        unnest(lineup) as ext_player_id
    from {{ ref('fct_point_lineups') }}
    {% if is_incremental() %}
    where season >= cast(extract(year from current_date) as int)
      and ext_game_id not in (select ext_game_id from {{ this }})
    {% endif %}
),

points as (
    -- Player spine: points/seconds played per player per game (game-accurate team from lineups)
    select
        ext_game_id,
        team_id,
        ext_player_id,
        max(season) as season,
        sum(seconds_played) as seconds_played,
        count(distinct case when line_type = 'O-Line' then point_id end) as o_points_played,
        count(distinct case when line_type = 'D-Line' then point_id end) as d_points_played,
        count(distinct case when line_type = 'O-Line' and is_stint_scoring then point_id end) as o_points_scored,
        count(distinct case when line_type = 'D-Line' and is_stint_scoring then point_id end) as d_points_scored
    from lineups
    group by 1, 2, 3
),

throws as (
    -- Metrics where the player was the thrower
    select
        ext_game_id,
        ext_thrower_id as ext_player_id,
        sum(case when is_assist then 1 else 0 end) as assists,
        sum(case when is_hockey_assist then 1 else 0 end) as hockey_assists,
        sum(case when is_completion then 1 else 0 end) as completions,
        sum(case when is_throwaway then 1 else 0 end) as throwaways,
        sum(case when is_stall then 1 else 0 end) as stalls,
        count(*) as throws_attempted,
        sum(yards_thrown) as yards_thrown,
        sum(case when throw_type = 'huck' and is_completion then 1 else 0 end) as hucks_completed,
        sum(case when throw_type = 'huck' then 1 else 0 end) as hucks_attempted,
        sum(case when throw_type = 'pass' and is_completion then 1 else 0 end) as pass_completed,
        sum(case when throw_type = 'pass' then 1 else 0 end) as pass_attempted,
        sum(case when throw_type = 'dump' and is_completion then 1 else 0 end) as dump_completed,
        sum(case when throw_type = 'dump' then 1 else 0 end) as dump_attempted,
        sum(case when throw_type = 'swing' and is_completion then 1 else 0 end) as swing_completed,
        sum(case when throw_type = 'swing' then 1 else 0 end) as swing_attempted
    from {{ ref('fct_throws') }}
    group by 1, 2
),

catches as (
    -- Metrics where the player was the receiver
    select
        ext_game_id,
        ext_receiver_id as ext_player_id,
        sum(case when is_completion and is_assist then 1 else 0 end) as goals,
        sum(case when is_completion then 1 else 0 end) as catches,
        sum(case when is_drop then 1 else 0 end) as drops,
        sum(yards_received) as yards_received
    from {{ ref('fct_throws') }}
    where ext_receiver_id is not null
    group by 1, 2
),

blocks as (
    -- Defensive blocks/callahans, attributed from fct_throws (user decision)
    select
        ext_game_id,
        ext_defender_id as ext_player_id,
        sum(case when is_block then 1 else 0 end) as blocks,
        sum(case when is_callahan then 1 else 0 end) as callahans
    from {{ ref('fct_throws') }}
    where ext_defender_id is not null
    group by 1, 2
),

pulls as (
    select
        ext_game_id,
        ext_puller_id as ext_player_id,
        count(*) as pulls,
        sum(case when is_out_of_bounds then 1 else 0 end) as ob_pulls,
        count(hangtime_seconds) as recorded_pulls,
        avg(hangtime_seconds) as recorded_pulls_hangtime
    from {{ ref('fct_pulls') }}
    group by 1, 2
)

select
    p.ext_game_id,
    p.team_id,
    p.ext_player_id,
    p.season,
    coalesce(t.assists, 0) as assists,
    coalesce(c.goals, 0) as goals,
    coalesce(t.hockey_assists, 0) as hockey_assists,
    coalesce(t.completions, 0) as completions,
    coalesce(t.throwaways, 0) as throwaways,
    coalesce(t.stalls, 0) as stalls,
    coalesce(t.throws_attempted, 0) as throws_attempted,
    coalesce(c.catches, 0) as catches,
    coalesce(c.drops, 0) as drops,
    coalesce(b.blocks, 0) as blocks,
    coalesce(b.callahans, 0) as callahans,
    coalesce(pl.pulls, 0) as pulls,
    coalesce(pl.ob_pulls, 0) as ob_pulls,
    coalesce(pl.recorded_pulls, 0) as recorded_pulls,
    round(coalesce(pl.recorded_pulls_hangtime, 0.0), 2) as recorded_pulls_hangtime,
    p.o_points_played,
    p.o_points_scored,
    p.d_points_played,
    p.d_points_scored,
    coalesce(p.seconds_played, 0) as seconds_played,
    coalesce(c.yards_received, 0) as yards_received,
    coalesce(t.yards_thrown, 0) as yards_thrown,
    coalesce(t.hucks_completed, 0) as hucks_completed,
    coalesce(t.hucks_attempted, 0) as hucks_attempted,
    coalesce(t.pass_completed, 0) as pass_completed,
    coalesce(t.pass_attempted, 0) as pass_attempted,
    coalesce(t.dump_completed, 0) as dump_completed,
    coalesce(t.dump_attempted, 0) as dump_attempted,
    coalesce(t.swing_completed, 0) as swing_completed,
    coalesce(t.swing_attempted, 0) as swing_attempted
from points p
left join throws t on p.ext_game_id = t.ext_game_id and p.ext_player_id = t.ext_player_id
left join catches c on p.ext_game_id = c.ext_game_id and p.ext_player_id = c.ext_player_id
left join blocks b on p.ext_game_id = b.ext_game_id and p.ext_player_id = b.ext_player_id
left join pulls pl on p.ext_game_id = pl.ext_game_id and p.ext_player_id = pl.ext_player_id
