"""SQL dataset queries for the forecasting pipeline.

Holds the feature-engineering SQL registered in `QUERY_REGISTRY`. The
`player_game_stats` query reads `mart_player_game_stats` and, per player, builds
game-1/2/3 lag features and 5-game rolling averages for every metric alongside
the current-game actuals.
"""

from typing import Dict

player_game_stats_dataset_query = r"""
    WITH dataset AS (
        SELECT 
            season,
            game_date,
            ext_game_id,
            team_id,
            ext_team_id,
            ext_player_id,
            opponent_team_id,
            opponent_ext_team_id,

            -- 1. Actuals for the current game
            COLUMNS(* EXCLUDE (season, game_date, ext_game_id, team_id, ext_team_id, opponent_team_id, opponent_ext_team_id, ext_player_id)),
            
            -- 2. Game-1 Lags for all metrics (e.g., goals_lag1, assists_lag1)
            LAG(COLUMNS(* EXCLUDE (season, game_date, ext_game_id, team_id, ext_team_id, opponent_team_id, opponent_ext_team_id, ext_player_id)), 1) 
                OVER player_window AS "\0_lag1",
            LAG(COLUMNS(* EXCLUDE (season, game_date, ext_game_id, team_id, ext_team_id, opponent_team_id, opponent_ext_team_id, ext_player_id)), 2) 
                OVER player_window AS "\0_lag2",
            LAG(COLUMNS(* EXCLUDE (season, game_date, ext_game_id, team_id, ext_team_id, opponent_team_id, opponent_ext_team_id, ext_player_id)), 3) 
                OVER player_window AS "\0_lag3",
                
            -- 3. 5-Game Rolling Averages for all metrics (e.g., goals_predicted, assists_predicted)
            AVG(COLUMNS(* EXCLUDE (season, game_date, ext_game_id, team_id, ext_team_id, opponent_team_id, opponent_ext_team_id, ext_player_id))) 
                OVER rolling_window AS "\0_rolling"

        FROM mart_player_game_stats
        WINDOW 
            player_window AS (
                PARTITION BY ext_player_id 
                ORDER BY game_date
            ),
            rolling_window AS (
                PARTITION BY ext_player_id 
                ORDER BY game_date 
                ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
            )
        ORDER BY 
            ext_player_id, 
            game_date
    )

    SELECT * FROM dataset;
    """

QUERY_REGISTRY: Dict[str, str] = {
    "player_game_stats": player_game_stats_dataset_query,
}

