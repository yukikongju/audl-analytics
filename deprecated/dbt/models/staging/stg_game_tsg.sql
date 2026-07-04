with source as (
    select * from {{ source('audl', 'game_tsg') }}
), renamed as (
    select 
	id, 
	teamSeasonId as team_season_id,
	gameId as game_id,
	source,
	startOnOffense as start_on_offense,
	events,
	updateMoment as update_moment,
	statusId as status_id,
	scoreTimesOur as score_times_our,
	scoreTimesTheir as score_times_their,
	completionsNumer as completions_numer,
	completionsDenom as completions_denom,
	hucksNumer as hucks_numer,
	hucksDenom as hucks_denom,
	blocks,
	turnovers,
	oLineScores as offensive_line_scores,
	oLinePoints as offensive_line_points,
	oLinePossessions as offensive_line_possessions,
	dLineScores as defensive_line_scores,
	dLinePoints as defensive_line_points,
	dLinePossessions as defensive_line_possessions,
	redZoneScores as red_zone_scores,
	redZonePossessions as red_zone_possessions,
	isHome as is_home,
	rosterIds as roster_ids
    from source
)

select * from renamed
