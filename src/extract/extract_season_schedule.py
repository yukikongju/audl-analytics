import argparse
import logging

from audl.stats.endpoints.seasonschedule import SeasonSchedule

def main(args) -> None:
    # --- parse arguments
    season = args.season
    user = args.user
    password = args.password
    host = args.host
    port = args.port
    db = args.db
    table_name = args.table_name

    # --- verify arguments
    if not (2020 <= season <= 2025):
        raise ValueError("Season needs to be an integer between 2020 and 2025")

    df_schedule = get_season_schedule(season)

    # --- TODO: create db connection


    # --- TODO: push to postgres


def get_season_schedule(season: int):
    schedule = SeasonSchedule(season).get_schedule()
    return schedule


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest Season Games to Postgres")

    parser.add_argument("--season", required=True, type=int, help="Season to extract game from")
    parser.add_argument("--user", required=True, help="username for postgres")
    parser.add_argument("--password", required=True, help="password for postgres")
    parser.add_argument("--host", required=True, help="host for postgres")
    parser.add_argument("--port", required=True, help="port for postgres")
    parser.add_argument("--db", required=True, help="database for postgres")
    parser.add_argument("--table_name", required=True, help="table name for postgres")

    args = parser.parse_args()
    main(args)

