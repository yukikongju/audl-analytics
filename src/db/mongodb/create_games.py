import json
import os

from src.utils.connections import get_mongo_db

def main():
    db = get_mongo_db()
    ROOT_DIR = os.path.abspath(os.curdir)
    GAME_SCHEMA_JSON_PATH = os.path.join(ROOT_DIR, "src/db/mongodb/schema/games1.json")

    try: 
        with open(GAME_SCHEMA_JSON_PATH) as f:
            game_schema = json.load(f)
    except Exception as e:
        raise FileNotFoundError(f"Could not find file: {e}")

    db.create_collection("games", **game_schema)

if __name__ == "__main__":
    main()
