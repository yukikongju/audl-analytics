-- Grain: one row per (ext_game_id, id) where id = roster entry id. Fails if duplicated.
select ext_game_id, id, count(*) as n
from {{ ref('stg_player_game_metadata') }}
group by 1, 2
having count(*) > 1
