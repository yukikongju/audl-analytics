# ER Modeling - Game Events

**Source**


**Intermediate**



**Facts Table**

- [X] `fct_team_game_stats` => player_game_stats aggregate should match stg_tsg
    * team_season_id: int
    * game_id: int
    * start_on_offense: bool
    * scoreTimes: [int]
    * completionsNumer: int
    * completionsDenom: int
    * hucksNumer: int
    * hucksDenom: int
    * blocks: int
    * turnovers: int
    * oLineScores: int
    * oLinePoints: int
    * oLinePossessions: int
    * dLineScores: int
    * dLinePoints: int
    * dLinePossessions: int
    * redZoneScores: int
    * redZonePossessions: int
    * isHome: bool
    * derived metrics:
	+ completion_perc: float
	+ huck_perc
	+ hold_perc: oLineScores / oLinePoints
	+ break_perc: dLineScores / dLinePoints
	+ offensive_line_conversions: oLineScores / oLinePossessions
	+ defensive_line_conversions: dLineScores / dLinePossessions
	+ red_zone_conversions: redZoneScores / redZonePossessions
- `fct_passes`: TBD
    * id
    * game_id
    * team_id
    * possession_id
    * thrower_id: int
    * receiver_id: int | None
    * x
    * y
- `fct_blocks`
    * 
- `fct_timeouts`
- `fct_game_points_lineup`
    * id
    * game_id
    * team_id
    * lineupIds
- [X] `fct_player_game_stats` 
    * ext_player_id
    * ext_game_id
    * PP, OPP, DPP, MP 
    * AST, GLS, BLK, HA, T, S, C, D
    * throwing_yards, receiving_yards, 
    * cmp, 
    * derived metrics:
	+ plus_minus
	+ cmp%
	+ total_yards
	+ offensive_efficiency
- `fct_game_score_times`
    * game_id
    * team_id
    * score_time

**Dim Table**

- [X] `dim_season_team`
    * id
    * team_id
    * season_id
    * division_id
    * city
    * abbrev
    * ulti_analytics_ext_id
    * name
    * ext_team_id
    * ls_team_id
    * active
    * primary_hex
    * secondary_hex
- [X] `dim_season_players`
    * id
    * team_season_id
    * player_id
    * jersey_number
    * active
    * first_name
    * last_name
    * ext_player_id
    * ls_player_id
- [X] `dim_game`
    * id
    * team_season_id_home
    * team_season_id_away
    * status_id
    * score_home
    * score_away
    * live
    * reg_season
    * ignore_game
    * lock
    * ext_game_id
    * start_timestamp
    * start_timezone
    * start_time_tbd
    * aw_section
    * update_timestamp
    * location_id
    * ls_game_id
    * ticket_url
    * streaming_url
    * type_id

**Aggregation Tables**

- `agg_player_season_game_stats` => player game stats by season
- `agg_team_season_game_stats` => team game stats by season
- `agg_player_throw_completions` => completion rate  and distribution for each type of throw

Ideas:
- Team performance against each other as the season progress

## Analytics Table

**Graph**

- `player_game_edges`: "plays in"
- `player_player_edges`: "plays"
- `player_scd_table` => ???
    * player_name, scoring_class, is_active, start_season, end_date, current_season
- `team_vertices`

**Cumulative Tables Ideas**

- Player-Centric Cumulative Tables
    * Player performance trend => rolling average of players stats for the last 15 games
- Team-Level Cumulative Tables
    * Team Seasons Stats => Cumulative Performance across games
    * Head-to-Head matchup: cumulative performance against specific teams
	+ team_id, opponent_id, wins, losses, avg_goals_diff (in the last 10 games)
- Time-Based Cumulative Tables
    * Quarterly Performance Cumulative => avg points scored per quarter over the season
    * Comeback tracker
    * Clutch Stats => cumulative stats in final minutes of close games
- Advanced
    * Fatigue => track cumulative minutes played over time, rest days, back-to-back games
    * Elo rating => 

**Cumulative Tables Schema**

- Team Head to Head
    * `agg_team_head_to_head_by_season`
	+ keys: team_id, opponent_id, season_id
	+ metrics:
    * `cum_team_head_to_head`
	+ keys: team_id, opponent_id, season_id
	+ metrics: [last 30 games] => array
	+ derived_metrics:
- Player Elo Rating
    * `agg_player_stats`
    * `player_stats_cumulated`
	+ keys: player_id
	+ metrics: [last 30 games] =>
	+ derived metrics

**Analytical Patterns**

- Funnel Analysis
- Grouping Sets
- Growth Accounting
- Retention Analysis
- Window Based Analysis

## Resources

- [Zach Wilson - Data Engineering Handbook](https://github.com/DataExpert-io/data-engineer-handbook/blob/main/bootcamp/materials/1-dimensional-data-modeling/lecture-lab/player_game_edges.sql)

