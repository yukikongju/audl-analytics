select
    {{ dbt_utils.generate_surrogate_key(['stg_game_metadata.id']) }} as game_key,
    stg_game_metadata.id,
    stg_game_metadata.team_season_id_home,
    stg_game_metadata.team_season_id_away,
    --  stg_game_metadata.status_id,
    stg_game_metadata.reg_season,
    stg_game_metadata.ext_game_id,
    stg_game_metadata.start_timestamp,
    stg_game_metadata.start_timezone,
    stg_game_metadata.division_str,
    --  stg_game_metadata.update_timestamp,
    stg_game_metadata.location_id,
    stg_game_metadata.ls_game_id,
    stg_game_metadata.ticket_url,
    stg_game_metadata.streaming_url,
    stg_game_metadata.type_id
from {{ ref('stg_game_metadata') }}
