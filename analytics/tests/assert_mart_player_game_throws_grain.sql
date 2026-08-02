-- Grain: one row per (ext_game_id, ext_thrower_id, ext_receiver_id). Fails if duplicated.
select ext_game_id, ext_thrower_id, ext_receiver_id, count(*) as n
from {{ ref('mart_player_game_throws') }}
group by 1, 2, 3
having count(*) > 1
