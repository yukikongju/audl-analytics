"""AUDL/UFA staging pipeline entrypoint.

Given an external game id (e.g. ``2026-05-10-MTL-PIT``), fetch the two raw sources and
write the four staging tables as JSON to ``outputs/<game_id>/``:

    outputs/<game_id>/stg_throws.json
    outputs/<game_id>/stg_pulls.json
    outputs/<game_id>/stg_point_lineups.json
    outputs/<game_id>/stg_games.json

Usage:
    uv run audl-pipeline 2026-05-10-MTL-PIT
    uv run audl-pipeline 2026-05-10-MTL-PIT --local   # read local sample files, no network
    uv run audl-pipeline 2026-05-10-MTL-PIT --out-dir outputs

    # or as a module: uv run python -m main 2026-05-10-MTL-PIT
"""

import argparse
from pathlib import Path

from pipeline_utils import (
    BASE_URL,
    game_date,
    http_get_json,
    load_local_game,
    load_local_game_events,
    write_json,
)
from timeline import build_timeline
from transform_games import extract_games
from transform_point_lineups import extract_point_lineups_events
from transform_pulls import extract_pulls_events
from transform_throws import extract_throws_events


def fetch_game_data(ext_game_id):
    """GET the game-stats JSON (``game``/``rosters``/``tsgHome``/``tsgAway``)."""
    return http_get_json(f"{BASE_URL}/stats-pages/game/{ext_game_id}")


def fetch_game_events_data(ext_game_id):
    """GET the gameEvents JSON (``data.homeEvents`` / ``data.awayEvents``)."""
    return http_get_json(f"{BASE_URL}/api/v1/gameEvents?gameID={ext_game_id}")


def run(ext_game_id, out_dir="outputs", local=False, dump_raw=False):
    """Fetch, transform, and write the four staging tables. Returns a name->rows dict.

    The three gameEvents transforms share one timeline, so it's built once here and passed
    in. With ``dump_raw`` the two raw payloads are also written to ``<out_dir>/<id>/raw/``.
    """
    if local:
        game_json = load_local_game(ext_game_id)
        events_json = load_local_game_events(ext_game_id)
    else:
        game_json = fetch_game_data(ext_game_id)
        events_json = fetch_game_events_data(ext_game_id)

    ctx = {
        "game_id": ext_game_id,
        "start_timestamp": game_json["game"]["start_timestamp"],
        "date": game_date(ext_game_id),
        "home_team_id": game_json["game"]["team_season_id_home"],
        "away_team_id": game_json["game"]["team_season_id_away"],
    }

    data = events_json["data"]
    timeline = build_timeline(
        data["homeEvents"], data["awayEvents"],
        ctx["home_team_id"], ctx["away_team_id"], where=ctx["game_id"],
    )

    tables = {
        "stg_throws": extract_throws_events(timeline, ctx),
        "stg_pulls": extract_pulls_events(timeline, ctx),
        "stg_point_lineups": extract_point_lineups_events(timeline, ctx),
        "stg_games": extract_games(game_json),
    }

    out = Path(out_dir) / ext_game_id
    if dump_raw:
        for name, payload in (("game", game_json), ("game_events", events_json)):
            write_json(payload, out / "raw" / f"{name}.json")
    for name, rows in tables.items():
        path = write_json(rows, out / "staging" / f"{name}.json")
        print(f"  {name:20s} {len(rows):5d} rows -> {path}")

    return tables


def arg_parse():
    p = argparse.ArgumentParser(description="Build AUDL staging tables for a game.")
    p.add_argument("ext_game_id", help="external game id, e.g. 2026-05-10-MTL-PIT")
    p.add_argument("--out-dir", default="outputs", help="output directory (default: outputs)")
    p.add_argument("--local", action="store_true",
                   help="read local sample files instead of fetching")
    p.add_argument("--dump-raw", action="store_true",
                   help="also write the raw game/gameEvents payloads to <out-dir>/<id>/raw/")
    return p.parse_args()


def main():
    args = arg_parse()
    print(f"Building staging tables for {args.ext_game_id}")
    run(args.ext_game_id, out_dir=args.out_dir, local=args.local, dump_raw=args.dump_raw)


if __name__ == "__main__":
    main()
