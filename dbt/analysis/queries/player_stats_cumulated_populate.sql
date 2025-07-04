with yesterday as (
    select * from player_stats_cumulated
    where date = DATE(CURRENT_DATE() - interval 1 Day)
), today as (
    select
	ps.user_id, -- FIXME: currently ext_user_id
	DATE_TRUNC('day', g.start_timestamp) as today_date,

	-- atomic metrics
	ps.last30_assists,
	ps.last30_goals,
	ps.last30_hockey_assists,
	ps.last30_completions,
	ps.last30_throwaways,
	ps.last30_stalls,
	ps.last30_throws_attempted,
	ps.last30_catches,
	ps.last30_drops,
	ps.last30_blocks,
	ps.last30_callahans,
	ps.last30_pulls,
	ps.last30_out_of_bound_pulls,
	ps.last30_recorded_pulls,
	ps.last30_recorded_pulls_hang_time,
	ps.last30_offensive_points_played,
	ps.last30_offensive_points_scored,
	ps.last30_defensive_points_played,
	ps.last30_defensive_points_scored,
	ps.last30_seconds_played,
	ps.last30_yards_received,
	ps.last30_yards_thrown,
	ps.last30_hucks_completed,
	ps.last30_hucks_attempted
    from {{ ref('fct_player_game_stats') }} as ps
    join {{ ref('dim_games') }} as g
    on ps.game_id = g.game_id
    where g.start_timestamp = DATE_TRUNC('day', CURRENT_DATE())
), combined as (
    select 
	COALESCE(y.user_id, t.user_id) as user_id,
	COALESCE(t.today_date, y.date + Interval '1 day') as date,

	COALESCE(IF(t.user_id is null,
		y.last30_assists,
		IF(CARDINALITY(y.last30_assists < 30), 
		    ARRAY[t.assists] || y.last30_assists, 
		    ARRAY[t.assists] || REVERSE(SLICE(REVERSE(y.last30_assists, 2, 29)))
		)
	)) as last30_assists,
	COALESCE(IF(t.user_id is null,
		y.last30_goals,
		IF(CARDINALITY(y.last30_goals < 30), 
		    ARRAY[t.assists] || y.last30_goals, 
		    ARRAY[t.assists] || REVERSE(SLICE(REVERSE(y.last30_goals, 2, 29)))
		)
	)) as last30_goals,
	COALESCE(IF(t.user_id is null,
		y.last30_hockey_assists,
		IF(CARDINALITY(y.last30_hockey_assists< 30), 
		    ARRAY[t.assists] || y.last30_hockey_assists, 
		    ARRAY[t.assists] || REVERSE(SLICE(REVERSE(y.last30_hockey_assists, 2, 29))))
	)) as last30_hockey_assists,
	COALESCE(
	  IF(t.user_id IS NULL,
	    y.last30_completions,
	    IF(CARDINALITY(y.last30_completions) < 30,
	      ARRAY[t.completions] || y.last30_completions,
	      ARRAY[t.completions] || REVERSE(SLICE(REVERSE(y.last30_completions), 2, 29))
	    )
	  )
	) AS last30_completions,

	COALESCE(
	  IF(t.user_id IS NULL,
	    y.last30_throwaways,
	    IF(CARDINALITY(y.last30_throwaways) < 30,
	      ARRAY[t.throwaways] || y.last30_throwaways,
	      ARRAY[t.throwaways] || REVERSE(SLICE(REVERSE(y.last30_throwaways), 2, 29))
	    )
	  )
	) AS last30_throwaways,

	COALESCE(
	  IF(t.user_id IS NULL,
	    y.last30_stalls,
	    IF(CARDINALITY(y.last30_stalls) < 30,
	      ARRAY[t.stalls] || y.last30_stalls,
	      ARRAY[t.stalls] || REVERSE(SLICE(REVERSE(y.last30_stalls), 2, 29))
	    )
	  )
	) AS last30_stalls,

	COALESCE(
	  IF(t.user_id IS NULL,
	    y.last30_throws_attempted,
	    IF(CARDINALITY(y.last30_throws_attempted) < 30,
	      ARRAY[t.throws_attempted] || y.last30_throws_attempted,
	      ARRAY[t.throws_attempted] || REVERSE(SLICE(REVERSE(y.last30_throws_attempted), 2, 29))
	    )
	  )
	) AS last30_throws_attempted,

	COALESCE(
	  IF(t.user_id IS NULL,
	    y.last30_catches,
	    IF(CARDINALITY(y.last30_catches) < 30,
	      ARRAY[t.catches] || y.last30_catches,
	      ARRAY[t.catches] || REVERSE(SLICE(REVERSE(y.last30_catches), 2, 29))
	    )
	  )
	) AS last30_catches,

	COALESCE(
	  IF(t.user_id IS NULL,
	    y.last30_drops,
	    IF(CARDINALITY(y.last30_drops) < 30,
	      ARRAY[t.drops] || y.last30_drops,
	      ARRAY[t.drops] || REVERSE(SLICE(REVERSE(y.last30_drops), 2, 29))
	    )
	  )
	) AS last30_drops,

	COALESCE(
	  IF(t.user_id IS NULL,
	    y.last30_blocks,
	    IF(CARDINALITY(y.last30_blocks) < 30,
	      ARRAY[t.blocks] || y.last30_blocks,
	      ARRAY[t.blocks] || REVERSE(SLICE(REVERSE(y.last30_blocks), 2, 29))
	    )
	  )
	) AS last30_blocks,

	COALESCE(
	  IF(t.user_id IS NULL,
	    y.last30_callahans,
	    IF(CARDINALITY(y.last30_callahans) < 30,
	      ARRAY[t.callahans] || y.last30_callahans,
	      ARRAY[t.callahans] || REVERSE(SLICE(REVERSE(y.last30_callahans), 2, 29))
	    )
	  )
	) AS last30_callahans,

	COALESCE(
	  IF(t.user_id IS NULL,
	    y.last30_pulls,
	    IF(CARDINALITY(y.last30_pulls) < 30,
	      ARRAY[t.pulls] || y.last30_pulls,
	      ARRAY[t.pulls] || REVERSE(SLICE(REVERSE(y.last30_pulls), 2, 29))
	    )
	  )
	) AS last30_pulls,

	COALESCE(
	  IF(t.user_id IS NULL,
	    y.last30_out_of_bound_pulls,
	    IF(CARDINALITY(y.last30_out_of_bound_pulls) < 30,
	      ARRAY[t.out_of_bound_pulls] || y.last30_out_of_bound_pulls,
	      ARRAY[t.out_of_bound_pulls] || REVERSE(SLICE(REVERSE(y.last30_out_of_bound_pulls), 2, 29))
	    )
	  )
	) AS last30_out_of_bound_pulls,

	COALESCE(
	  IF(t.user_id IS NULL,
	    y.last30_recorded_pulls,
	    IF(CARDINALITY(y.last30_recorded_pulls) < 30,
	      ARRAY[t.recorded_pulls] || y.last30_recorded_pulls,
	      ARRAY[t.recorded_pulls] || REVERSE(SLICE(REVERSE(y.last30_recorded_pulls), 2, 29))
	    )
	  )
	) AS last30_recorded_pulls,

	COALESCE(
	  IF(t.user_id IS NULL,
	    y.last30_recorded_pulls_hang_time,
	    IF(CARDINALITY(y.last30_recorded_pulls_hang_time) < 30,
	      ARRAY[t.recorded_pulls_hang_time] || y.last30_recorded_pulls_hang_time,
	      ARRAY[t.recorded_pulls_hang_time] || REVERSE(SLICE(REVERSE(y.last30_recorded_pulls_hang_time), 2, 29))
	    )
	  )
	) AS last30_recorded_pulls_hang_time,

	COALESCE(
	  IF(t.user_id IS NULL,
	    y.last30_offensive_points_played,
	    IF(CARDINALITY(y.last30_offensive_points_played) < 30,
	      ARRAY[t.offensive_points_played] || y.last30_offensive_points_played,
	      ARRAY[t.offensive_points_played] || REVERSE(SLICE(REVERSE(y.last30_offensive_points_played), 2, 29))
	    )
	  )
	) AS last30_offensive_points_played,

	COALESCE(
	  IF(t.user_id IS NULL,
	    y.last30_offensive_points_scored,
	    IF(CARDINALITY(y.last30_offensive_points_scored) < 30,
	      ARRAY[t.offensive_points_scored] || y.last30_offensive_points_scored,
	      ARRAY[t.offensive_points_scored] || REVERSE(SLICE(REVERSE(y.last30_offensive_points_scored), 2, 29))
	    )
	  )
	) AS last30_offensive_points_scored,

	COALESCE(
	  IF(t.user_id IS NULL,
	    y.last30_defensive_points_played,
	    IF(CARDINALITY(y.last30_defensive_points_played) < 30,
	      ARRAY[t.defensive_points_played] || y.last30_defensive_points_played,
	      ARRAY[t.defensive_points_played] || REVERSE(SLICE(REVERSE(y.last30_defensive_points_played), 2, 29))
	    )
	  )
	) AS last30_defensive_points_played,

	COALESCE(
	  IF(t.user_id IS NULL,
	    y.last30_defensive_points_scored,
	    IF(CARDINALITY(y.last30_defensive_points_scored) < 30,
	      ARRAY[t.defensive_points_scored] || y.last30_defensive_points_scored,
	      ARRAY[t.defensive_points_scored] || REVERSE(SLICE(REVERSE(y.last30_defensive_points_scored), 2, 29))
	    )
	  )
	) AS last30_defensive_points_scored,

	COALESCE(
	  IF(t.user_id IS NULL,
	    y.last30_seconds_played,
	    IF(CARDINALITY(y.last30_seconds_played) < 30,
	      ARRAY[t.seconds_played] || y.last30_seconds_played,
	      ARRAY[t.seconds_played] || REVERSE(SLICE(REVERSE(y.last30_seconds_played), 2, 29))
	    )
	  )
	) AS last30_seconds_played,

	COALESCE(
	  IF(t.user_id IS NULL,
	    y.last30_yards_received,
	    IF(CARDINALITY(y.last30_yards_received) < 30,
	      ARRAY[t.yards_received] || y.last30_yards_received,
	      ARRAY[t.yards_received] || REVERSE(SLICE(REVERSE(y.last30_yards_received), 2, 29))
	    )
	  )
	) AS last30_yards_received,

	COALESCE(
	  IF(t.user_id IS NULL,
	    y.last30_yards_thrown,
	    IF(CARDINALITY(y.last30_yards_thrown) < 30,
	      ARRAY[t.yards_thrown] || y.last30_yards_thrown,
	      ARRAY[t.yards_thrown] || REVERSE(SLICE(REVERSE(y.last30_yards_thrown), 2, 29))
	    )
	  )
	) AS last30_yards_thrown,

	COALESCE(
	  IF(t.user_id IS NULL,
	    y.last30_hucks_completed,
	    IF(CARDINALITY(y.last30_hucks_completed) < 30,
	      ARRAY[t.hucks_completed] || y.last30_hucks_completed,
	      ARRAY[t.hucks_completed] || REVERSE(SLICE(REVERSE(y.last30_hucks_completed), 2, 29))
	    )
	  )
	) AS last30_hucks_completed,

	COALESCE(
	  IF(t.user_id IS NULL,
	    y.last30_hucks_attempted,
	    IF(CARDINALITY(y.last30_hucks_attempted) < 30,
	      ARRAY[t.hucks_attempted] || y.last30_hucks_attempted,
	      ARRAY[t.hucks_attempted] || REVERSE(SLICE(REVERSE(y.last30_hucks_attempted), 2, 29))
	    )
	  )
	) AS last30_hucks_attempted


    from yesterday as y
    full outer join today as t
    on y.user_id = t.user_id
)

--  insert into player_stats_cumulated

select
    user_id,
    AVG(unnest(last30_assists)) as avg_assists, 
    AVG(unnest(last30_goals)) as avg_goals, 
    AVG(unnest(last30_hockey_assists)) as avg_hockey_assists, 
    AVG(unnest(last30_completions)) as avg_completions, 
    AVG(unnest(last30_throwaways)) as avg_throwaways, 
    AVG(unnest(last30_stalls)) as avg_stalls, 
    AVG(unnest(last30_throws_attempted)) as avg_throws_attempted, 
    AVG(unnest(last30_catches)) as avg_catches, 
    AVG(unnest(last30_drops)) as avg_drops, 
    AVG(unnest(last30_callahans)) as avg_callahans, 
    AVG(unnest(last30_pulls)) as avg_pulls, 
    AVG(unnest(last30_out_of_bound_pulls)) as avg_out_of_bound_pulls, 
    AVG(unnest(last30_recorded_pulls)) as avg_recorded_pulls, 
    AVG(unnest(last30_recorded_pulls_hang_time)) as avg_recorded_pulls_hang_time, 
    AVG(unnest(last30_offensive_points_scored)) as avg_offensive_points_scored, 
    AVG(unnest(last30_offensive_points_played)) as avg_offensive_points_played, 
    AVG(unnest(last30_defensive_points_scored)) as avg_defensive_points_scored, 
    AVG(unnest(last30_defensive_points_played)) as avg_defensive_points_played, 
    AVG(unnest(last30_seconds_played)) as avg_seconds_played, 
    AVG(unnest(last30_yards_received)) as avg_yards_received, 
    AVG(unnest(last30_yards_thrown)) as avg_yards_thrown, 
    AVG(unnest(last30_hucks_completed)) as avg_hucks_completed, 
    AVG(unnest(last30_hucks_attempted)) as avg_hucks_attempted, 

    -- TODO: derived metrics

from combined


