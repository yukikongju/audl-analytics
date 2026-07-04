"""Seasonal extraction job.

Pulls the season-level reference data (players, teams, games) for a year and writes each
to the Hive-partitioned data lake (under ``AUDL_SOURCE_DIR``) as JSON:

    <SOURCE_DIR>/players/season=<year>/players.json
    <SOURCE_DIR>/teams/season=<year>/teams.json
    <SOURCE_DIR>/games/season=<year>/games.json

Each ufastats endpoint returns ``{"object": ..., "data": [...]}``; we persist the ``data``
records. Existing files are skipped unless ``--override`` is passed, so re-runs are cheap.

Usage:
    uv run audl-extract-seasonal --year 2026
    uv run audl-extract-seasonal --year 2026 --override
"""

import argparse
import logging
from datetime import date
from pathlib import Path
from typing import Union

from pipeline_utils import BASE_URL, http_get_json, source_dir, write_json

# Configure basic logging for the pipeline
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# entity -> (subdir, api path template)
ENDPOINTS = {
    "players": ("players", "players?years={year}"),
    "teams": ("teams", "teams?years={year}"),
    "games": ("games", "games?date={year}"),
}


def run(year: int, data_dir: Union[str, Path, None] = None, override: bool = False) -> None:
    """Fetch and write the three seasonal tables for ``year``."""
    data_dir = Path(data_dir).expanduser() if data_dir else source_dir()

    for entity, (subdir, path_tpl) in ENDPOINTS.items():
        target = data_dir / subdir / f"season={year}" / f"{subdir}.json"
        
        if target.exists() and not override:
            logger.info(f"  {entity:8s} skip (exists) -> {target}")
            continue
        
        # Ensure the destination directory exists before writing
        target.parent.mkdir(parents=True, exist_ok=True)
        
        url = f"{BASE_URL}/api/v1/{path_tpl.format(year=year)}"
        
        try:
            response = http_get_json(url)
            # Use .get() to avoid KeyErrors if the API response shape changes unexpectedly
            records = response.get("data", [])
            
            write_json(records, target)
            logger.info(f"  {entity:8s} {len(records):5d} records -> {target}")
            
        except Exception as e:
            # Catching general exceptions so one failed endpoint doesn't kill the whole job
            logger.error(f"  {entity:8s} FAILED to process: {e}")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    p = argparse.ArgumentParser(description="Extract seasonal AUDL reference data (players/teams/games).")
    p.add_argument("--year", type=int, default=date.today().year,
                   help="season year (default: current year)")
    p.add_argument("--data-dir", default=None,
                   help="data lake root (default: $AUDL_SOURCE_DIR)")
    p.add_argument("--override", action="store_true",
                   help="overwrite existing files (default: skip existing)")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    logger.info(f"Extracting seasonal data for {args.year}")
    run(year=args.year, data_dir=args.data_dir, override=args.override)


if __name__ == "__main__":
    main()
