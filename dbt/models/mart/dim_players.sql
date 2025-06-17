select 
    distinct {{ dbt_utils.generate_surrogate_key(['stg_game_rosters.id']) }} as player_key,
    stg_game_rosters.id,
    stg_game_rosters.team_season_id,
    stg_game_rosters.player_id,
    stg_game_rosters.jersey_number,
    stg_game_rosters.active,
    stg_game_rosters.first_name,
    stg_game_rosters.last_name,
    stg_game_rosters.ext_player_id,
    stg_game_rosters.ls_player_id
from {{ ref('stg_game_rosters') }}
