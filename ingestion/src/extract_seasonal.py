"""Seasonal extraction job.

Pulls the season-level reference data (players, teams, games) for a year and writes each
to the year-partitioned data lake as JSON:

    ~/Data/AUDLStats/<year>/players/players<year>.json
    ~/Data/AUDLStats/<year>/teams/teams<year>.json
    ~/Data/AUDLStats/<year>/games/games<year>.json

Each ufastats endpoint returns ``{"object": ..., "data": [...]}``; we persist the ``data``
records. Existing files are skipped unless ``--override`` is passed, so re-runs are cheap.

Usage:
    uv run audl-extract-seasonal --year 2026
    uv run audl-extract-seasonal --year 2026 --override
"""

import argparse
from datetime import date
from pathlib import Path

from pipeline_utils import BASE_URL, http_get_json, write_json

# entity -> (subdir, api path template)
ENDPOINTS = {
    "players": ("players", "players?years={year}"),
    "teams": ("teams", "teams?years={year}"),
    "games": ("games", "games?date={year}"),
}


def run(year, data_dir, override=False):
    """Fetch and write the three seasonal tables for ``year``."""
    data_dir = Path(data_dir).expanduser()
    for entity, (subdir, path_tpl) in ENDPOINTS.items():
        target = data_dir / str(year) / subdir / f"{subdir}{year}.json"
        if target.exists() and not override:
            print(f"  {entity:8s} skip (exists) -> {target}")
            continue
        url = f"{BASE_URL}/api/v1/{path_tpl.format(year=year)}"
        records = http_get_json(url)["data"]
        write_json(records, target)
        print(f"  {entity:8s} {len(records):5d} records -> {target}")


def arg_parse():
    p = argparse.ArgumentParser(description="Extract seasonal AUDL reference data (players/teams/games).")
    p.add_argument("--year", type=int, default=date.today().year,
                   help="season year (default: current year)")
    p.add_argument("--data-dir", default="~/Data/AUDLStats",
                   help="data lake root (default: ~/Data/AUDLStats)")
    p.add_argument("--override", action="store_true",
                   help="overwrite existing files (default: skip existing)")
    return p.parse_args()


def main():
    args = arg_parse()
    print(f"Extracting seasonal data for {args.year}")
    run(args.year, args.data_dir, override=args.override)


if __name__ == "__main__":
    main()
