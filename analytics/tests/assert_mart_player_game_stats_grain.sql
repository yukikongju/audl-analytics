-- Grain: one row per (ext_game_id, team_id, ext_player_id). Fails if duplicated.
select ext_game_id, team_id, ext_player_id, count(*) as n
from {{ ref('mart_player_game_stats') }}
group by 1, 2, 3
having count(*) > 1
