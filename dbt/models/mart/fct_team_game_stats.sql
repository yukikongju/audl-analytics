select
    id,
    team_season_id,
    source,
    start_on_offense,
    score_times_our as score_times,
    is_home,
    roster_ids,

    -- metrics
    completions_numer,
    completions_denom,
    huckes_numer,
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

    -- TODO: rates
    case when completions_denom > 0 
	then completions_numer / completions_denom 
	else null
    end as completion_perc,


from {{ ref('stg_game_tsg') }}
