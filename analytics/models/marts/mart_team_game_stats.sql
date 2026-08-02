{{ config(materialized='incremental', unique_key=['ext_game_id', 'team_id']) }}

with rollup as (
    -- Roll up individual player counts to the team level
    select
        ext_game_id,
        team_id,
        sum(assists) as team_assists,
        sum(goals) as team_goals,
        sum(hockey_assists) as team_hockey_assists,
        sum(completions) as team_completions,
        sum(throwaways) as team_throwaways,
        sum(stalls) as team_stalls,
        sum(throws_attempted) as team_throws_attempted,
        sum(catches) as team_catches,
        sum(drops) as team_drops,
        sum(blocks) as team_blocks,
        sum(callahans) as team_callahans,
        sum(pulls) as team_pulls,
        sum(ob_pulls) as team_ob_pulls,
        sum(yards_received) as team_yards_received,
        sum(yards_thrown) as team_yards_thrown,
        sum(hucks_completed) as team_hucks_completed,
        sum(hucks_attempted) as team_hucks_attempted
    from {{ ref('mart_player_game_stats') }}
    group by 1, 2
),

team_points as (
    -- Team-level point totals (distinct points, not a sum/max of players)
    select
        ext_game_id,
        team_id,
        count(distinct case when line_type = 'O-Line' then point_id end) as total_o_points_played,
        count(distinct case when line_type = 'D-Line' then point_id end) as total_d_points_played
    from {{ ref('fct_point_lineups') }}
    group by 1, 2
),

context as (
    -- fct_games is already one row per team; self-join for opponent context.
    -- team_season_id is the numeric team key that matches fct_point_lineups.team_id
    -- (ext_team_id is a slug like 'thunderbirds' and is kept for readability only).
    select
        g.ext_game_id,
        g.season,
        g.team_season_id as team_id,
        o.team_season_id as opponent_team_id,
        g.ext_team_id,
        o.ext_team_id as opponent_ext_team_id,
        g.is_home,
        g.score as team_score,
        o.score as opponent_score,
        (g.score > o.score) as is_win,
        g.o_line_scores,
        g.o_line_possessions,
        g.d_line_scores,
        g.d_line_possessions,
        g.red_zone_scores,
        g.red_zone_possessions
    from {{ ref('fct_games') }} g
    join {{ ref('fct_games') }} o
        on g.ext_game_id = o.ext_game_id
       and g.team_season_id <> o.team_season_id
)

select
    c.ext_game_id,
    c.team_id,
    c.opponent_team_id,
    c.ext_team_id,
    c.opponent_ext_team_id,
    c.is_home,
    c.is_win,
    c.team_score,
    c.opponent_score,
    r.team_assists,
    r.team_goals,
    r.team_hockey_assists,
    r.team_completions,
    r.team_throwaways,
    r.team_stalls,
    r.team_throws_attempted,
    r.team_catches,
    r.team_drops,
    r.team_blocks,
    r.team_callahans,
    r.team_pulls,
    r.team_ob_pulls,
    r.team_yards_received,
    r.team_yards_thrown,
    r.team_hucks_completed,
    r.team_hucks_attempted,
    tp.total_o_points_played,
    tp.total_d_points_played,
    c.o_line_possessions,
    c.o_line_scores,
    c.d_line_possessions,
    c.d_line_scores,
    c.red_zone_possessions,
    c.red_zone_scores,
    round(cast(c.o_line_scores as double) / nullif(c.o_line_possessions, 0), 4) as offensive_conversion_rate,
    round(cast(c.d_line_scores as double) / nullif(c.d_line_possessions, 0), 4) as defensive_break_rate,
    round(cast(c.red_zone_scores as double) / nullif(c.red_zone_possessions, 0), 4) as red_zone_conversion_rate
from context c
join rollup r on c.ext_game_id = r.ext_game_id and c.team_id = r.team_id
left join team_points tp on c.ext_game_id = tp.ext_game_id and c.team_id = tp.team_id
{% if is_incremental() %}
where c.season >= cast(extract(year from current_date) as int)
  and c.ext_game_id not in (select ext_game_id from {{ this }})
{% endif %}
