"""stg_games transform.

Built from the game-stats JSON (the ``stats-pages/game`` response), NOT gameEvents --
gameEvents carries no team ids or team-level summary fields. Produces two rows per game
(home + away), each a flat team-season record with the tsg summary stats plus the final
score and per-team scoring times. This is the source of team ids for the other transforms.
"""

import pandas as pd


def extract_games(game_json):
    """Return the stg_games rows (list of dicts, one per team) for a game.

    ``game_json`` is the raw ``stats-pages/game`` dict with ``game``, ``tsgHome`` and
    ``tsgAway``. Mirrors the drafted transform: normalise each tsg, graft on the final
    score / score times / external team id from ``game``, drop the bulky per-team event
    arrays, and concatenate.
    """
    game = game_json["game"]

    home = pd.json_normalize(game_json["tsgHome"])
    home.loc[:, "score"] = game["score_home"]
    home.loc[:, "score_times"] = str(game["score_times_home"])
    home.loc[:, "ext_team_id"] = game["team_season_home"]["team"]["ext_team_id"]

    away = pd.json_normalize(game_json["tsgAway"])
    away.loc[:, "score"] = game["score_away"]
    away.loc[:, "score_times"] = str(game["score_times_away"])
    away.loc[:, "ext_team_id"] = game["team_season_away"]["team"]["ext_team_id"]

    df_games = pd.concat([home, away], axis=0, ignore_index=True)
    df_games = df_games.drop(
        columns=["events", "scoreTimesOur", "scoreTimesTheir"], errors="ignore"
    )
    df_games.loc[:, "game_ext_id"] = game["ext_game_id"]

    return df_games.to_dict(orient="records")
