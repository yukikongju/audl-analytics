{{ config(materialized='incremental', unique_key=['ext_game_id', 'ext_thrower_id', 'ext_receiver_id']) }}

-- One row per thrower -> receiver connection per game, with throw-type distribution.
-- Only throws with a known receiver are counted (turnovers with no target are excluded).
select
    season,
    ext_game_id,
    ext_thrower_id,
    ext_receiver_id,
    sum(case when throw_type = 'huck' and is_completion then 1 else 0 end) as hucks_completed,
    sum(case when throw_type = 'huck' then 1 else 0 end) as hucks_attempted,
    sum(case when throw_type = 'pass' and is_completion then 1 else 0 end) as pass_completed,
    sum(case when throw_type = 'pass' then 1 else 0 end) as pass_attempted,
    sum(case when throw_type = 'dump' and is_completion then 1 else 0 end) as dump_completed,
    sum(case when throw_type = 'dump' then 1 else 0 end) as dump_attempted,
    sum(case when throw_type = 'swing' and is_completion then 1 else 0 end) as swing_completed,
    sum(case when throw_type = 'swing' then 1 else 0 end) as swing_attempted
from {{ ref('fct_throws') }}
where ext_receiver_id is not null
{% if is_incremental() %}
  and season >= cast(extract(year from current_date) as int)
  and ext_game_id not in (select ext_game_id from {{ this }})
{% endif %}
group by 1, 2, 3, 4
