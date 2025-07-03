import argparse
from typing import List

from sqlalchemy.sql import exists

from src.utils.postgres.connections import get_postgres_connection
from src.utils.postgres.operations import run_select_query
from src.utils.mongodb.connections import get_mongo_collection, get_mongo_db
from src.utils.mongodb.operations import upsert_document, find_all_documents_in_collection
from src.utils.validation.formatting import is_valid_date


def get_ext_game_ids(start_date: str, end_date: str) -> List[str]:
    # --- verify args type
    date_format =  '%Y-%m-%d'
    if not is_valid_date(start_date, date_format) or not is_valid_date(end_date, date_format):
        raise ValueError(f"start_date and end_date needs to be in format {date_format}")

    # --- get game schedule within dates
    conn = get_postgres_connection()
    query = f"select gameid from schedule where starttimestamp >= '{start_date}' and starttimestamp <= '{end_date}'"
    df = run_select_query(conn, query)
    ext_game_ids = list(df['gameid'])
    return ext_game_ids

def get_existing_ext_game_ids(start_date: str, end_date: str) -> List[str]:
    # --- verify args type
    date_format =  '%Y-%m-%d'
    if not is_valid_date(start_date, date_format) or not is_valid_date(end_date, date_format):
        raise ValueError(f"start_date and end_date needs to be in format {date_format}")

    # --- find documents
    predicate = {"game.start_timestamp": {"$gte": f"{start_date}", "$lt": f"{end_date}"}}
    included_fields = {"game.ext_game_id": 1, "_id": 0}

    db = get_mongo_db()
    documents = find_all_documents_in_collection(db=db, collection_name=COLLECTION_NAME, predicate=predicate, included_fields=included_fields)

    existing_ext_game_ids = [doc['game']['ext_game_id'] for doc in documents]
    return existing_ext_game_ids


def main(start_date: str, end_date: str):
    #  ext_game_ids = get_ext_game_ids(start_date, end_date)
    #  print(ext_game_ids)

    # --- get games already in MongoDB document
    existing_ext_game_ids = get_existing_ext_game_ids(start_date, end_date)
    print(existing_ext_game_ids)


    # --- TODO: get the games we need to fetch

    # --- TODO: insert document into MongoDB
    pass


if __name__ == "__main__":
    COLLECTION_NAME = "game-events"
    parser = argparse.ArgumentParser(description="Extracting all game events within dates")
    parser.add_argument("--start_date", type=str, help="Start date in format 'YYYY-MM-DD'")
    parser.add_argument("--end_date", type=str, help="End date in format 'YYYY-MM-DD'")

    args = parser.parse_args()
    main(args.start_date, args.end_date)
