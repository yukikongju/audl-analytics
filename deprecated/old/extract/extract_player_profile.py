from argparse import ArgumentParser
from audl.stats.endpoints.playerprofile import PlayerProfile

from src.utils.postgres.connections import get_postgres_connection
from src.utils.postgres.operations import upsert_dataframe, convert_df_types_to_table_schema
from src.utils.dataframe.cleanup import standardize_dataframe


def extract_player_profile(ext_player_id: str):
    # --- extract the data
    profile = PlayerProfile(ext_player_id)
    df = profile.get_personal_information()
    TABLE_NAME = "players"

    # --- push into Postgres
    conn = get_postgres_connection()
    df_clean = standardize_dataframe(df=df, case="snake")
    df_clean = convert_df_types_to_table_schema(conn, df_clean, TABLE_NAME)
    #  print(df_clean.columns)
    upsert_dataframe(conn, TABLE_NAME, df_clean)
    print(f"Successfully added player profile for player {ext_player_id}")


if __name__ == "__main__":
    parser = ArgumentParser(description="Ingest Player Profile to postgres 'players' table")

    parser.add_argument("--ext_player_id", required=True, type=str, help="Player external ID as found in their player profile ; ex: profile https://watchufa.com/league/players/amerriman would be 'amerriman'")

    args = parser.parse_args()
    ext_player_id=args.ext_player_id
    extract_player_profile(ext_player_id)
