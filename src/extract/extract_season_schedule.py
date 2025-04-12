import argparse
import logging
import pandas as pd

from argparse import ArgumentParser

from audl.stats.endpoints.seasonschedule import SeasonSchedule
from src.utils.postgres.connections import get_postgres_connection
from src.utils.postgres.operations import upsert_dataframe


def main(args: ArgumentParser) -> None:
    # --- parse arguments
    season = args.season
    SCHEDULE_TABLE_NAME = "schedule"

    # --- verify arguments
    if not (2020 <= season <= 2025):
        raise ValueError("Season needs to be an integer between 2020 and 2025")

    try:
        df_schedule = get_season_schedule(season)
    except Exception as e:
        raise ConnectionError(f"The following error occured when fetching the season schedule: {e}")

    # --- TODO: verify types

    # --- push to postgres
    conn = get_postgres_connection()
    upsert_dataframe(conn, SCHEDULE_TABLE_NAME, df_schedule)
    print(f"Successfully upserted dataframe into table {SCHEDULE_TABLE_NAME}")


def get_season_schedule(season: int) -> pd.DataFrame:
    schedule = SeasonSchedule(season).get_schedule()
    return schedule


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest Season Games to Postgres")

    parser.add_argument("--season", required=True, type=int, help="Season to extract game from")

    args = parser.parse_args()
    main(args)

