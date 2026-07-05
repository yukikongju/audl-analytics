"""AUDL/UFA processing pipeline entrypoint.

Given an external game id (e.g. ``2026-05-10-MTL-PIT``), read the raw extracted payloads
from ``AUDL_SOURCE_DIR`` (no network) and write the five ``ext_*`` tables to the
Hive-partitioned ``AUDL_PROCESSED_DIR`` data lake, one file per game (parquet or json):

    <PROCESSED_DIR>/ext_throws/season=<year>/month=<MM>/<game_id>.<fmt>
    <PROCESSED_DIR>/ext_pulls/season=<year>/month=<MM>/<game_id>.<fmt>
    <PROCESSED_DIR>/ext_point_lineups/season=<year>/month=<MM>/<game_id>.<fmt>
    <PROCESSED_DIR>/ext_blocks/season=<year>/month=<MM>/<game_id>.<fmt>
    <PROCESSED_DIR>/ext_games/season=<year>/month=<MM>/<game_id>.<fmt>

Requires the game to have been extracted first, in the same ``--format`` (``audl-extract-weekly``).

Usage:
    uv run audl-pipeline 2026-05-10-MTL-PIT
    uv run audl-pipeline 2026-05-10-MTL-PIT --format json
    uv run audl-pipeline 2026-05-10-MTL-PIT --source-dir /tmp/src --processed-dir /tmp/out

    # or as a module: uv run python -m main 2026-05-10-MTL-PIT
"""

import argparse
from pathlib import Path

from pipeline_utils import (
    FORMATS,
    data_suffix,
    game_date,
    game_month,
    game_year,
    load_source_game_events,
    load_source_game_stats,
    partition_dir,
    processed_dir,
    write_table,
)
from timeline import build_timeline
from transform_blocks import extract_blocks_events
from transform_games import extract_games
from transform_point_lineups import extract_point_lineups_events
from transform_pulls import extract_pulls_events
from transform_throws import extract_throws_events


def run(ext_game_id, source_root=None, processed_root=None, fmt="parquet"):
    """Read raw payloads from SOURCE_DIR, transform, and write the five ext_* tables.

    Returns a name->rows dict. The three gameEvents transforms share one timeline, so it's
    built once here and passed in. Reads only from the data lake — no network access.
    Both reads and writes use ``fmt`` (``parquet`` or ``json``).
    """
    game_json = load_source_game_stats(ext_game_id, source_root, fmt)
    # Extraction already unwrapped ``response["data"]``, so this is the inner dict.
    data = load_source_game_events(ext_game_id, source_root, fmt)

    ctx = {
        "game_id": ext_game_id,
        "start_timestamp": game_json["game"]["start_timestamp"],
        "date": game_date(ext_game_id),
        "home_team_id": game_json["game"]["team_season_id_home"],
        "away_team_id": game_json["game"]["team_season_id_away"],
    }

    timeline = build_timeline(
        data["homeEvents"], data["awayEvents"],
        ctx["home_team_id"], ctx["away_team_id"], where=ctx["game_id"],
    )

    tables = {
        "ext_throws": extract_throws_events(timeline, ctx),
        "ext_pulls": extract_pulls_events(timeline, ctx),
        "ext_point_lineups": extract_point_lineups_events(timeline, ctx),
        "ext_blocks": extract_blocks_events(timeline, ctx),
        "ext_games": extract_games(game_json),
    }

    root = Path(processed_root) if processed_root else processed_dir()
    year, month = game_year(ext_game_id), game_month(ext_game_id)
    for name, rows in tables.items():
        path = write_table(rows, partition_dir(root, name, year, month) / f"{ext_game_id}{data_suffix(fmt)}")
        print(f"  {name:20s} {len(rows):5d} rows -> {path}")

    return tables


def arg_parse():
    p = argparse.ArgumentParser(description="Build AUDL ext_* tables for a game.")
    p.add_argument("ext_game_id", help="external game id, e.g. 2026-05-10-MTL-PIT")
    p.add_argument("--source-dir", default=None,
                   help="data lake root to read from (default: $AUDL_SOURCE_DIR)")
    p.add_argument("--processed-dir", default=None,
                   help="data lake root to write to (default: $AUDL_PROCESSED_DIR)")
    p.add_argument("--format", dest="fmt", choices=FORMATS, default="parquet",
                   help="data file format for reads and writes (default: parquet)")
    return p.parse_args()


def main():
    args = arg_parse()
    print(f"Building ext tables for {args.ext_game_id} ({args.fmt})")
    run(args.ext_game_id, source_root=args.source_dir, processed_root=args.processed_dir, fmt=args.fmt)


if __name__ == "__main__":
    main()
