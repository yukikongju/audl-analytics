import pandas as pd


def model(dbt, session):
    dbt.config(
        materialized="incremental",
        unique_key=["ext_game_id", "id"],
        packages=["pandas"],
    )

    df = dbt.source("raw", "game_stats").df()

    seen = set()
    if dbt.is_incremental:
        seen = set(
            session.sql(f"SELECT DISTINCT ext_game_id FROM {dbt.this}")
            .df()["ext_game_id"]
            .tolist()
        )

    records = []
    for rec in df.to_dict(orient="records"):
        game = rec["game"]
        ext_game_id = game["ext_game_id"]
        if ext_game_id in seen:
            continue
        for is_home, roster_key, ts_key in (
            (True, "rostersHome", "team_season_home"),
            (False, "rostersAway", "team_season_away"),
        ):
            roster = rec.get(roster_key)
            if roster is None:  # LIST columns arrive as numpy arrays; avoid ambiguous truthiness
                continue
            # Players in rostersHome/Away belong to the game's home/away team_season, which is
            # present for every game. Derive team_season_id/ext_team_id from it rather than the
            # entry-level fields, which the API only returns for 2021-2024 games.
            team_season = game.get(ts_key) or {}
            team_season_id = team_season.get("id")
            ext_team_id = (team_season.get("team") or {}).get("ext_team_id")
            for entry in roster:
                row = dict(entry)  # id, jersey_number, player{first_name, last_name, ...}
                # nested player.id duplicates entry-level player_id (same value) and would
                # collide once flattened to "player_id".
                if isinstance(row.get("player"), dict):
                    row["player"] = {k: v for k, v in row["player"].items() if k != "id"}
                row["team_season_id"] = team_season_id
                row["ext_team_id"] = ext_team_id
                row["ext_game_id"] = ext_game_id
                row["is_home"] = is_home
                records.append(row)

    if not records:
        # incremental run with no new games: return correct schema, zero rows
        if dbt.is_incremental:
            return session.sql(f"SELECT * FROM {dbt.this} WHERE 1=0").df()
        return pd.DataFrame(records)

    return pd.json_normalize(records, sep="_")
