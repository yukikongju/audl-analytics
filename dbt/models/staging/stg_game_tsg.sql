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
	updateMoment,
	statusId as status_id,
	scoreTimesOur as score_times_our,
	scoreTimesTheir as score_times_their,
	completionsNumer as completions_numer,
	completionsDenom as completions_denom,
	hucksNumer as hucks_numer,
	hucksDenom as hucks_denom,
	blocks,
	turnovers,
	oLineScores,
	oLinePoints,
	oLinePossessions,
	dLineScores,
	dLinePoints,
	dLinePossessions,
	redZoneScores,
	redZonePossessions,
	isHome,
	rosterIds
    from source
)

select * from renamed
