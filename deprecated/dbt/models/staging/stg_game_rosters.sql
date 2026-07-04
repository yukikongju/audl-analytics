with source as (
    select * from {{ source('audl', 'game_rosters') }}
), renamed as (
    select
	id, 
	team_season_id,
	player_id,
	jersey_number,
	active,
	player_first_name as first_name,
	player_last_name as last_name,
	player_ext_player_id as ext_player_id,
	player_ls_player_id as ls_player_id
    from source
)

select * from renamed
