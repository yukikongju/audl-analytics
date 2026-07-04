select
	distinct {{ dbt_utils.generate_surrogate_key(['stg_game_metadata.home_id']) }} as team_key,
	stg_game_metadata.home_id as id,
	stg_game_metadata.home_team_id as team_id,
	stg_game_metadata.home_season_id as season_id,
	stg_game_metadata.home_division_id as division_id,
	stg_game_metadata.home_city as city,
	stg_game_metadata.home_abbrev as abbrev,
	stg_game_metadata.home_ulti_analytics_ext_id as ulti_analytics_ext_id,
	stg_game_metadata.home_team_name as team_name,
	stg_game_metadata.home_ext_team_id as ext_team_id,
	stg_game_metadata.home_ls_team_id as lst_team_id,
	stg_game_metadata.home_team_primary_hex as primary_hex,
	stg_game_metadata.home_team_secondary_hex as secondary_hex
from {{ ref('stg_game_metadata') }}
