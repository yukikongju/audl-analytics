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
        for is_home, key in ((True, "team_season_home"), (False, "team_season_away")):
            team_season = game.get(key)
            if not team_season:
                continue
            row = dict(team_season)  # id, team_id, season_id, division_id, city, abbrev, ..., team{...}
            # Drop the nested team.id: it duplicates the top-level team_id and would
            # collide with it once flattened (both -> "team_id").
            if isinstance(row.get("team"), dict):
                row["team"] = {k: v for k, v in row["team"].items() if k != "id"}
            row["ext_game_id"] = ext_game_id
            row["is_home"] = is_home
            records.append(row)

    if not records:
        # incremental run with no new games: return correct schema, zero rows
        if dbt.is_incremental:
            return session.sql(f"SELECT * FROM {dbt.this} WHERE 1=0").df()
        return pd.DataFrame(records)

    return pd.json_normalize(records, sep="_")
