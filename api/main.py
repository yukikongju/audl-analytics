import os
import duckdb
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi_pagination import Page, add_pagination, paginate
#  from pydantic import BaseModel


#### Database Configuration
AUDL_ANALYTICS_DIR = os.getenv("AUDL_ANALYTICS_DIR", ".")
DB_FILENAME = os.getenv("AUDL_ANALYTICS_DB", "dev.duckdb")
DB_PATH = os.path.join(AUDL_ANALYTICS_DIR, DB_FILENAME)

app = FastAPI(title="AUDL Analytics API")
add_pagination(app)

#### UTILITIES

def get_db():
    """Dependency to get a read-only DuckDB connection per request."""
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail=f"Database not found at {DB_PATH}")

    try:
        conn = duckdb.connect(DB_PATH, read_only=True)
    except duckdb.IOException as e: 
        raise HTTPException(status_code=503, detail=f"Database is locked by another process: {e}")

    try:
        yield conn
    finally:
        conn.close()

def execute_query(db: duckdb.DuckDBPyConnection, query: str, params: list = None) -> List[Dict[str, Any]]:
    """Helper function to execute a query and return a list of dictionaries."""
    try:
        cursor = db.execute(query, params or [])
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

#### ENDPOINTS

@app.get("/api/v1/player-throws", response_model=List[Dict[str, Any]])
def get_player_throws(
    season: int, 
    ext_player_id: str, 
    db: duckdb.DuckDBPyConnection = Depends(get_db)
):
    q2 = """
        SELECT * 
        FROM fct_throws 
        WHERE season = ? AND ext_thrower_id = ?
    """
    return execute_query(db, q2, [season, ext_player_id])

@app.get("/api/v1/player-stats", response_model=List[Dict[str, Any]])
def get_player_stats(
    season: int, 
    ext_player_id: str, 
    db: duckdb.DuckDBPyConnection = Depends(get_db)
):
    query = """
        SELECT * 
        FROM mart_player_game_stats 
        WHERE season = ? AND ext_player_id = ?
    """
    # Note: Corrected ext_thrower_id to ext_player_id based on table schema context
    return execute_query(db, query, [season, ext_player_id])

@app.get("/api/v1/team-stats", response_model=List[Dict[str, Any]])
def get_team_stats(
    season: int, 
    ext_team_id: str, 
    db: duckdb.DuckDBPyConnection = Depends(get_db)
):
    query = """
        SELECT * 
        FROM mart_team_game_stats 
        WHERE season = ? AND ext_team_id = ?
    """
    return execute_query(db, query, [season, ext_team_id])

@app.get("/api/v1/team-roster", response_model=List[Dict[str, Any]])
def get_team_roster(
    season: int, 
    ext_team_id: str, 
    per: str = Query("total", pattern="^(game|total)$"),
    db: duckdb.DuckDBPyConnection = Depends(get_db)
):
    query = r"""
        SELECT
            ext_player_id,
            COUNT(*) as game_played,
            SUM(COLUMNS(* EXCLUDE (ext_game_id, game_date, season, team_id, ext_team_id, ext_player_id))) as "sum_\0", 
            AVG(COLUMNS(* EXCLUDE (ext_game_id, game_date, season, team_id, ext_team_id, ext_player_id))) as "avg_\0"
        FROM mart_player_game_stats 
        WHERE season = ? AND ext_team_id = ?
        GROUP BY 1
    """
    return execute_query(db, query, [season, ext_team_id])

@app.get("/api/v1/player-leaderboard", response_model=Page[Dict[str, Any]])
def get_player_leaderboard(
    season: int,
    per: str = Query("total", pattern="^(game|total)$"),
    db: duckdb.DuckDBPyConnection = Depends(get_db)
):
    query = r"""
        SELECT
            ext_player_id,
            COUNT(*) as game_played,
            SUM(COLUMNS(* EXCLUDE (ext_game_id, game_date, season, team_id, ext_team_id, ext_player_id))) as "sum_\0",
            AVG(COLUMNS(* EXCLUDE (ext_game_id, game_date, season, team_id, ext_team_id, ext_player_id))) as "avg_\0"
        FROM mart_player_game_stats
        WHERE season = ?
        GROUP BY 1
    """
    return paginate(execute_query(db, query, [season]))

@app.get("/api/v1/team-leaderboard", response_model=Page[Dict[str, Any]])
def get_team_leaderboard(
    season: int,
    per: str = Query("total", pattern="^(game|total)$"),
    db: duckdb.DuckDBPyConnection = Depends(get_db)
):
    query = r"""
        SELECT
            ext_team_id,
            COUNT(*) AS games_played,
            SUM(CAST(is_win AS INT)) AS wins,
            SUM(COLUMNS(* EXCLUDE (
                ext_game_id, season, game_date, team_id, ext_team_id,
                opponent_team_id, opponent_ext_team_id, is_home, is_win
            ))) AS "sum_\0",
            AVG(COLUMNS(* EXCLUDE (
                ext_game_id, season, game_date, team_id, ext_team_id,
                opponent_team_id, opponent_ext_team_id, is_home, is_win
            ))) AS "avg_\0"
        FROM mart_team_game_stats
        WHERE season = ?
        GROUP BY ext_team_id
        ORDER BY 1;
    """
    return paginate(execute_query(db, query, [season]))

@app.get("/api/v1/player-metadata", response_model=List[Dict[str, Any]])
def get_player_throws(
    season: Optional[str] = None, 
    ext_player_id: Optional[str] = None, 
    ext_team_id: Optional[str] = None, 
    db: duckdb.DuckDBPyConnection = Depends(get_db)
):
    # 1. Start with your base query and required parameters
    query = "SELECT * FROM dim_players"
    params = []
    
    # 2. Append to the query and parameters if the optional value exists
    # building: SELECT * FROM dim_players WHERE season = ? AND ext_player_id = ? AND ...
    filters = {
        "season": season,
        "ext_player_id": ext_player_id,
        "ext_team_id": ext_team_id
    }
    conditions = {k: v for k, v in filters.items() if v is not None} # only keep the condition that are not None
    if conditions:
        query += " WHERE " + " AND ".join(f"{col} = ?" for col in conditions)
        params = list(conditions.values())

    return execute_query(db, query, params)


@app.get("/api/v1/team-metadata", response_model=List[Dict[str, Any]])
def get_player_throws(
    season: Optional[str] = None, 
    ext_team_id: Optional[str] = None, 
    db: duckdb.DuckDBPyConnection = Depends(get_db)
):
    # 1. Start with your base query and required parameters
    query = "SELECT * FROM dim_teams"
    params = []
    
    # 2. Append to the query and parameters if the optional value exists
    # building: SELECT * FROM dim_players WHERE season = ? AND ext_player_id = ? AND ...
    filters = {
        "season": season,
        "ext_team_id": ext_team_id
    }
    conditions = {k: v for k, v in filters.items() if v is not None} # only keep the condition that are not None
    if conditions:
        query += " WHERE " + " AND ".join(f"{col} = ?" for col in conditions)
        params = list(conditions.values())

    return execute_query(db, query, params)

@app.get("/api/v1/schedule", response_model=List[Dict[str, Any]])
def get_player_throws(
    season: int,
    db: duckdb.DuckDBPyConnection = Depends(get_db)
):
    # 1. Start with your base query and required parameters
    query = "SELECT * FROM mart_schedule WHERE season = ?"
    return execute_query(db, query, [season])



