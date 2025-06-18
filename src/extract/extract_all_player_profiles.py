import pandas as pd

from src.extract.extract_player_profile import extract_player_profile
from src.utils.dataframe.loading import read_csv

def main():
    # --- read ext_player_id from dbt/seeds/
    EXT_PLAYER_IDS_FILE_PATH = "dbt/seeds/ext_player_ids.csv"
    df = read_csv(file_path=EXT_PLAYER_IDS_FILE_PATH)

    ext_player_ids = list(df['ext_player_id'])
    for ext_player_id in ext_player_ids:
        # TODO: check if user is already in table

        print(f"Extracting profile for {ext_player_id}")
        try:
            extract_player_profile(ext_player_id)
            print(f"Successfully extracted player profile {ext_player_id}")
        except:
            print(f"An error occured when extracting the profile for {ext_player_id}. Skipping...")
            

if __name__ == "__main__":
    main()
