import logging

from audl.stats.endpoints.gamestats import GameStats
from argparse import ArgumentParser, Namespace
from src.utils.mongodb.connections import get_mongo_db
from src.utils.mongodb.operations import upsert_document


def main(args: Namespace):
    ext_game_id = args.ext_game_id 
    COLLECTION_NAME = "game-events"

    # "Game id is invalid. Please check!"
    try: 
        game = GameStats(ext_game_id)
        game_json = game.json
    except Exception as e:
        raise ConnectionError(f"A connection error has occured: {e}")

    # --- push into database
    db = get_mongo_db()
    upsert_id = upsert_document(db, COLLECTION_NAME, {"game.ext_game_id": ext_game_id}, game_json)
    logging.log(0, f"Successfully upsert game {ext_game_id} into table {COLLECTION_NAME}")



if __name__ == "__main__":
    parser = ArgumentParser(description="Ingest Season Games to Postgres")

    parser.add_argument("--ext_game_id", required=True, type=str, help="Game ID ; ex: '2022-07-31-DET-MIN'")

    args = parser.parse_args()
    main(args)
