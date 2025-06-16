from argparse import ArgumentParser, Namespace
import pandas as pd

from src.utils.mongodb.connections import get_mongo_document
from src.utils.postgres.operations import upsert_dataframe
from src.utils.postgres.connections import get_postgres_connection
from src.utils.dataframe.cleanup import standardize_dataframe


def main(args: Namespace):
    # --- get document from ext_game_id
    ext_game_id = args.ext_game_id 
    COLLECTION_NAME = "game-events"
    query = {"game.ext_game_id": ext_game_id}
    document = get_mongo_document(COLLECTION_NAME, query)

    # --- push tables into postgres
    conn = get_postgres_connection()

    # get game metadata
    df_games = pd.json_normalize(document['game'])
    df_games = standardize_dataframe(df=df_games, case="snake")
    upsert_dataframe(conn=conn, table_name='game_metadata', df=df_games)

    # get game tsg
    df_tsgHome = pd.json_normalize(document['tsgHome'])
    df_tsgHome = standardize_dataframe(df=df_tsgHome, case="snake")
    upsert_dataframe(conn=conn, table_name='game_tsg', df=df_tsgHome)

    df_tsgAway = pd.json_normalize(document['tsgAway'])
    df_tsgAway = standardize_dataframe(df=df_tsgAway, case="snake")
    upsert_dataframe(conn=conn, table_name='game_tsg', df=df_tsgAway)

    # get game rosters
    df_rostersHome = pd.json_normalize(document['rostersHome'])
    df_rostersHome = standardize_dataframe(df=df_rostersHome, case="snake")
    upsert_dataframe(conn=conn, table_name='game_rosters', df=df_rostersHome)

    df_rostersAway = pd.json_normalize(document['rostersAway'])
    df_rostersAway = standardize_dataframe(df=df_rostersAway, case="snake")
    upsert_dataframe(conn=conn, table_name='game_rosters', df=df_rostersAway)


if __name__ == "__main__":
    parser = ArgumentParser(description="Loading Game Events into Postgres Tables")
    parser.add_argument("--ext_game_id", required=True, type=str, help="Game ID ; ex: '2022-07-31-DET-MIN'")
    args = parser.parse_args()
    main(args)

