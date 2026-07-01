#  import pandas as pd
from argparse import ArgumentParser, Namespace
from audl.stats.endpoints.playerprofile import PlayerProfile

from src.utils.postgres.connections import get_postgres_connection
from src.utils.postgres.operations import upsert_dataframe, convert_df_types_to_table_schema
from src.utils.dataframe.cleanup import standardize_dataframe

def main(args: Namespace):
    # --- extract the data
    ext_player_id = args.ext_player_id
    profile = PlayerProfile(ext_player_id)
    df = profile.get_season_games_stats(2025)
    TABLE_NAME = "player_game_stats"

    # --- push into Postgres
    conn = get_postgres_connection()
    df_clean = standardize_dataframe(df=df, case="lower")
    df_clean = convert_df_types_to_table_schema(conn, df_clean, TABLE_NAME)
    #  print(df_clean.columns)
    upsert_dataframe(conn, TABLE_NAME, df_clean)
    print(f"Successfully added game stats for player {ext_player_id}")


if __name__ == "__main__":
    parser = ArgumentParser(description="Ingest Player Game Stats to postgres 'player_game_stats' table")

    parser.add_argument("--ext_player_id", required=True, type=str, help="Player external ID as found in their player profile ; ex: profile https://watchufa.com/league/players/amerriman would be 'amerriman'")

    args = parser.parse_args()
    main(args)
