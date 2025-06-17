with source as (
    select * from {{ source('audl', 'game_metadata') }}
), renamed as (
    select 
	id,
	team_season_id_home,
	score_home,
	score_away,
	reg_season,
	start_timestamp,
	start_timezone,
	aw_section as division_str,
	score_times_home,
	score_times_away,
	location_id,
	ls_game_id,
	ticket_url,
	streaming_url,

	-- Home
	team_season_home_id as home_id,
	team_season_home_team_id as home_team_id,
	team_season_home_season_id as home_season_id,
	team_season_home_division_id as home_division_id,
	team_season_home_city as home_city,
	team_season_home_abbrev as home_abbrev,
	team_season_home_ulti_analytics_ext_id as home_ulti_analytics_ext_id,
	team_season_home_final_standing as home_final_standing,
	team_season_home_team_name as home_team_name,
	team_season_home_team_ext_team_id as home_ext_team_id,
	team_season_home_team_ls_team_id as home_ls_team_id,
	--  team_season_home_team_active as home_team_active,
	team_season_home_team_primary_hex as home_team_primary_hex,
	team_season_home_team_secondary_hex as home_team_secondary_hex,

	-- Away
	team_season_away_id as away_id,
	team_season_away_team_id as away_team_id,
	team_season_away_season_id as away_season_id,
	team_season_away_division_id as away_division_id,
	team_season_away_city as away_city,
	team_season_away_abbrev as away_abbrev,
	team_season_away_ulti_analytics_ext_id as away_ulti_analytics_ext_id,
	team_season_away_final_standing as away_final_standing,
	team_season_away_team_name as away_team_name,
	team_season_away_team_ext_team_id as away_team_ext_team_id,
	team_season_away_team_ls_team_id as away_team_ls_team_id,
	--  team_season_away_team_active as away_team_active,
	team_season_away_team_primary_hex as away_team_primary_hex,
	team_season_away_team_secondary_hex as away_team_secondary_hex
    from source
)

select * from renamed
