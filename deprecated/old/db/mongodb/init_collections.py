import os

from pymongo.database import Database
from src.utils.mongodb.connections import get_mongo_db
from src.utils.mongodb.operations import create_collection

def create_game_collections(db: Database):
    GAME_SCHEMA_JSON_PATH = os.path.join(ROOT_DIR, "src/db/mongodb/schema/games1.json")
    GAME_COLLECTION_NAME = "games"
    create_collection(db, GAME_COLLECTION_NAME, GAME_SCHEMA_JSON_PATH)

    # --- create indexes
    game_collection = db[GAME_COLLECTION_NAME]
    game_collection.create_index("game.ext_game_id", unique=True)

def create_player_game_stats(db: Database): # TODO
    pass



def main():
    db = get_mongo_db()

    #  create_game_collections(db)


if __name__ == "__main__":
    ROOT_DIR = os.path.abspath(os.curdir)
    main()
