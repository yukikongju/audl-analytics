-- Grain: one row per (ext_game_id, team_id); exactly two rows per game. Fails if duplicated.
select ext_game_id, team_id, count(*) as n
from {{ ref('mart_team_game_stats') }}
group by 1, 2
having count(*) > 1
