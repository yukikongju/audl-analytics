select
    ext_player_id,
    ext_game_id,

    -- atomic metrics
    assists,
    goals,
    hockey_assists,
    completions,
    throwaways,
    stalls,
    throws_attempted,
    catches,
    drops,
    blocks,
    callahans,
    pulls,
    out_of_bound_pulls,
    recorded_pulls,
    recorded_pulls_hang_time,
    offensive_points_played,
    offensive_points_scored,
    defensive_points_played,
    defensive_points_scored,
    seconds_played,
    yards_received,
    yards_thrown,
    hucks_completed,
    hucks_attempted,

    -- derived metrics
    assists + goals + blocks - throwaways - drops as plus_minus,
    case when throws_attempted > 0 
	then (throws_attempted - throwaways) / throws_attempted
	else null
    end as completion_perc,
    yards_received + yards_thrown as total_yards
from {{ ref('stg_player_game_stats') }}
