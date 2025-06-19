with source as (
    select * from {{ source('audl', 'player_game_stats') }}
), renamed as (
    select
	ext_player_id,
	gameid as game_id,
	ishome as is_home,
	scorehome as score_home,
	scoreaway as score_away,
	assists,
	goals,
	hockeyassists as hockey_assists,
	completions,
	throwaways,
	stalls,
	throwsattempted as throws_attempted,
	catches,
	drops,
	blocks,
	callahans,
	pulls,
	obpulls as out_of_bound_pulls,
	recordedpulls as recorded_pulls,
	recordedpullshangtime as recorded_pulls_hang_time,
	opointsplayed as offensive_points_played,
	opointsscored as offensive_points_scored,
	dpointsplayed as defensive_points_played,
	dpointsscored as defensive_points_scored,
	secondsplayed as seconds_played,
	yardsreceived as yards_received,
	huckscompleted as hucks_completed,
	hucksattempted as hucks_attempted
    from source
)

select * from renamed
