select
    id,
    team_season_id,
    source,
    start_on_offense,
    score_times_our as score_times,
    is_home,
    roster_ids,

    -- atomic metrics
    completions_numer,
    completions_denom,
    hucks_numer,
    hucks_denom,
    blocks,
    turnovers,
    offensive_line_scores,
    offensive_line_points,
    offensive_line_possessions,
    defensive_line_scores,
    defensive_line_points,
    defensive_line_possessions,
    red_zone_scores,
    red_zone_possessions,

    -- derived metrics
    case when completions_denom > 0 
	then completions_numer / completions_denom 
	else null
    end as completion_perc,
    case when hucks_denom > 0 
	then hucks_numer / hucks_denom 
	else null
    end as hucks_perc,
    case when offensive_line_points > 0 
	then offensive_line_scores / offensive_line_points 
	else null
    end as hold_perc,
    case when defensive_line_points > 0 
	then defensive_line_scores / defensive_line_points 
	else null
    end as break_perc,
    case when offensive_line_possessions > 0 
	then offensive_line_scores / offensive_line_possessions 
	else null
    end as offensive_line_conversion_perc,
    case when defensive_line_possessions > 0 
	then defensive_line_scores / defensive_line_possessions 
	else null
    end as defensive_line_conversion_perc,
    case when red_zone_possessions > 0 
	then red_zone_scores / red_zone_possessions 
	else null
    end as red_zone_conversion_perc

from {{ ref('stg_game_tsg') }}
