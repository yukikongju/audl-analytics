"""Weekly extraction job.

For every game played within a date window, pulls the per-game data (playerGameStats and
gameEvents) and writes each to the year-partitioned data lake as JSON:

    ~/Data/AUDLStats/<year>/player_game_stats/<gameID>.json
    ~/Data/AUDLStats/<year>/game_events/<gameID>.json

The window defaults to the last ~2 weeks (today-14 .. today-1), so a weekly cron picks up
newly-played games. The set of games is read from the seasonal games file, so run
``audl-extract-seasonal`` first. Existing files are skipped unless ``--override``.

Usage:
    uv run audl-extract-weekly --year 2026
    uv run audl-extract-weekly --year 2026 --start-date 2026-05-10 --end-date 2026-05-10
    uv run audl-extract-weekly --year 2026 --override
"""

import argparse
import json
from datetime import date, timedelta
from pathlib import Path

from pipeline_utils import BASE_URL, game_date, http_get_json, write_json

# entity -> (subdir, api path template keyed on gameID)
ENDPOINTS = {
    "player_game_stats": ("player_game_stats", "playerGameStats?gameID={game_id}"),
    "game_events": ("game_events", "gameEvents?gameID={game_id}"),
}


def load_games(data_dir, year):
    """Read the seasonal games records; raise a helpful error if not extracted yet."""
    games_file = data_dir / str(year) / "games" / f"games{year}.json"
    if not games_file.exists():
        raise SystemExit(
            f"games file not found: {games_file}\n"
            f"run `uv run audl-extract-seasonal --year {year}` first."
        )
    with open(games_file) as f:
        return json.load(f)


def fetch_game(data_dir, year, game_id, override=False):
    """Fetch + write both per-game tables for one game. Returns files written."""
    written = 0
    for entity, (subdir, path_tpl) in ENDPOINTS.items():
        target = data_dir / str(year) / subdir / f"{game_id}.json"
        if target.exists() and not override:
            continue
        url = f"{BASE_URL}/api/v1/{path_tpl.format(game_id=game_id)}"
        write_json(http_get_json(url)["data"], target)
        written += 1
    return written


def run(year, data_dir, start_date, end_date, override=False):
    """Fetch per-game data for all games with a date in [start_date, end_date]."""
    data_dir = Path(data_dir).expanduser()
    games = load_games(data_dir, year)

    selected = [g for g in games if start_date <= game_date(g["gameID"]) <= end_date]
    print(f"{len(selected)} game(s) in {start_date}..{end_date} (of {len(games)} total)")

    for g in selected:
        game_id = g["gameID"]
        try:
            written = fetch_game(data_dir, year, game_id, override=override)
            print(f"  {game_id}  {'skip' if written == 0 else f'{written} file(s)'}")
        except Exception as e:  # one bad game shouldn't abort the batch
            print(f"  {game_id}  WARNING: {e}")


def arg_parse():
    today = date.today()
    p = argparse.ArgumentParser(description="Extract per-game AUDL data (playerGameStats/gameEvents) for a date window.")
    p.add_argument("--year", type=int, default=today.year,
                   help="season year, locates the games file (default: current year)")
    p.add_argument("--data-dir", default="~/Data/AUDLStats",
                   help="data lake root (default: ~/Data/AUDLStats)")
    p.add_argument("--start-date", default=(today - timedelta(days=14)).isoformat(),
                   help="ISO start date, inclusive (default: today-14)")
    p.add_argument("--end-date", default=(today - timedelta(days=1)).isoformat(),
                   help="ISO end date, inclusive (default: today-1)")
    p.add_argument("--override", action="store_true",
                   help="overwrite existing files (default: skip existing)")
    return p.parse_args()


def main():
    args = arg_parse()
    print(f"Extracting weekly data for {args.year} ({args.start_date}..{args.end_date})")
    run(args.year, args.data_dir, args.start_date, args.end_date, override=args.override)


if __name__ == "__main__":
    main()
