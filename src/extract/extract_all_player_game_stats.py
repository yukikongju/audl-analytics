import pandas as pd
from audl.stats.endpoints.playerprofile import PlayerProfile
from src.utils.dataframe.loading import read_csv
from src.utils.postgres.connections import get_postgres_connection
from src.utils.postgres.operations import upsert_dataframe, convert_df_types_to_table_schema
from src.utils.dataframe.cleanup import standardize_dataframe


def main():
    # --- read ext_player_id from dbt/seeds/
    EXT_PLAYER_IDS_FILE_PATH = "dbt/seeds/ext_player_ids.csv"
    df = read_csv(file_path=EXT_PLAYER_IDS_FILE_PATH)
    ext_player_ids = list(df['ext_player_id'])

    dfs = []
    for ext_player_id in ext_player_ids:
        # TODO: check if user is already in table

        print(f"Extracting profile for {ext_player_id}")
        try:
            profile = PlayerProfile(ext_player_id)
            df = profile.get_season_games_stats(2025)
            dfs.append(df)
            print(f"Successfully extracted player game stats for {ext_player_id}")
        except:
            print(f"An error occured when extracting the profile for {ext_player_id}. Skipping...")

    df_all = pd.concat(dfs, axis=0)

    # --- 
    TABLE_NAME = "player_game_stats"
    conn = get_postgres_connection()
    df_clean = standardize_dataframe(df=df_all, case="lower")
    df_clean = convert_df_types_to_table_schema(conn, df_clean, TABLE_NAME)
    upsert_dataframe(conn, TABLE_NAME, df_clean)
    print(f"Successfully added data in player_game_stats table!")
            
if __name__ == "__main__":
    main()
