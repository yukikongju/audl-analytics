"""Weekly extraction job.

For every game played within a date window, pulls the per-game data (playerGameStats,
gameEvents, and the game-stats payload) and writes each to the Hive-partitioned data lake
(under ``AUDL_SOURCE_DIR``) as JSON:

    <SOURCE_DIR>/player_game_stats/season=<year>/month=<MM>/<gameID>.json
    <SOURCE_DIR>/game_events/season=<year>/month=<MM>/<gameID>.json
    <SOURCE_DIR>/game_stats/season=<year>/month=<MM>/<gameID>.json

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
import logging
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Union

from pipeline_utils import BASE_URL, game_date, game_month, http_get_json, source_dir, write_json

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# entity -> (subdir, full url template keyed on gameID, unwrap-"data")
# game_stats hits stats-pages/game (different base path) and is NOT wrapped in "data",
# so we persist the full payload as-is; the api/v1 endpoints are unwrapped to their "data".
ENDPOINTS = {
    "player_game_stats": ("player_game_stats", f"{BASE_URL}/api/v1/playerGameStats?gameID={{game_id}}", True),
    "game_events": ("game_events", f"{BASE_URL}/api/v1/gameEvents?gameID={{game_id}}", True),
    "game_stats": ("game_stats", f"{BASE_URL}/stats-pages/game/{{game_id}}", False),
}


def load_games(data_dir: Path, year: int) -> List[Dict[str, Any]]:
    """Read the seasonal games records; exit if not extracted yet."""
    games_file = data_dir / "games" / f"season={year}" / "games.json"
    
    if not games_file.exists():
        logger.error(
            f"Games file not found: {games_file}\n"
            f"Run `uv run audl-extract-seasonal --year {year}` first."
        )
        sys.exit(1)
        
    with open(games_file, "r") as f:
        return json.load(f)


def fetch_game(data_dir: Path, year: int, game_id: str, override: bool = False) -> int:
    """Fetch + write both per-game tables for one game. Returns number of files written."""
    written = 0
    for entity, (subdir, url_tpl, unwrap) in ENDPOINTS.items():
        target = data_dir / subdir / f"season={year}" / f"month={game_month(game_id)}" / f"{game_id}.json"

        if target.exists() and not override:
            continue

        # Ensure the destination directory exists
        target.parent.mkdir(parents=True, exist_ok=True)

        response = http_get_json(url_tpl.format(game_id=game_id))
        # api/v1 endpoints wrap payload in "data"; stats-pages/game returns it directly.
        records = response.get("data", []) if unwrap else response

        write_json(records, target)
        written += 1

    return written


def run(year: int, data_dir: Union[str, Path, None], start_date: str, end_date: str, override: bool = False) -> None:
    """Fetch per-game data for all games with a date in [start_date, end_date]."""
    data_dir = Path(data_dir).expanduser() if data_dir else source_dir()
    games = load_games(data_dir, year)

    selected = [g for g in games if start_date <= game_date(g["gameID"]) <= end_date]
    logger.info(f"{len(selected)} game(s) in {start_date}..{end_date} (of {len(games)} total)")

    for g in selected:
        game_id = g["gameID"]
        try:
            written = fetch_game(data_dir, year, game_id, override=override)
            status = "skip" if written == 0 else f"{written} file(s)"
            logger.info(f"  {game_id:20s} {status}")
        except Exception as e:
            # One bad game shouldn't abort the batch
            logger.warning(f"  {game_id:20s} FAILED: {e}")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    today = date.today()
    p = argparse.ArgumentParser(description="Extract per-game AUDL data (playerGameStats/gameEvents) for a date window.")
    p.add_argument("--year", type=int, default=today.year,
                   help="season year, locates the games file (default: current year)")
    p.add_argument("--data-dir", default=None,
                   help="data lake root (default: $AUDL_SOURCE_DIR)")
    p.add_argument("--start-date", default=(today - timedelta(days=14)).isoformat(),
                   help="ISO start date, inclusive (default: today-14)")
    p.add_argument("--end-date", default=(today - timedelta(days=1)).isoformat(),
                   help="ISO end date, inclusive (default: today-1)")
    p.add_argument("--override", action="store_true",
                   help="overwrite existing files (default: skip existing)")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    logger.info(f"Extracting weekly data for {args.year} ({args.start_date}..{args.end_date})")
    run(
        year=args.year,
        data_dir=args.data_dir,
        start_date=args.start_date,
        end_date=args.end_date,
        override=args.override
    )


if __name__ == "__main__":
    main()
