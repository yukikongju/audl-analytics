{{ config(materialized='table', unique_key=['ext_game_id']) }}

select
    c.season,
    c.ext_game_id,
    c.ext_away_team_id, 
    c.ext_home_team_id, 
    c.start_timestamp,
    c.start_timezone,
    c.streaming_url,
    c.week,    
    c.location,
    home.score as home_score,
    away.score as away_score,
    case 
        when home.ext_game_id is not null then 'Final'
        else 'Upcoming'
    end as status
from stg_calendar c
left join stg_games g on
    c.ext_game_id = g.ext_game_id
left join stg_games home on 
    c.ext_game_id = home.ext_game_id
    and home.is_home = true
left join stg_games away on 
    c.ext_game_id = away.ext_game_id
    and away.is_home = false


