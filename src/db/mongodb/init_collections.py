import json
import os

from pymongo.database import Database
from pymongo.errors import CollectionInvalid
from src.utils.mongodb.connections import get_mongo_db


def create_collection(db: Database, collection_name: str, schema_json_path: str | None = None) -> None:
    """
    Creates a MongoDB collection if it does not already exist.
    Optionally applies a validation schema from a JSON file.

    Parameters
    ----------
    db : pymongo.database.Database
        The MongoDB database object.
    collection_name : str
        The name of the collection to create.
    schema_json_path : str, optional
        Path to a JSON file containing the schema (with keys like 'validator', 'validationLevel', etc.).

    Raises
    ------
    FileNotFoundError
        If the schema file is provided but does not exist or cannot be read.
    ValueError
        If the schema file content is invalid.
    """
    if collection_name in db.list_collection_names():
        print(f"Collection '{collection_name}' already exists. Deleting it...")
        db[collection_name].drop()
        return

    schema = {}
    if schema_json_path:
        if not os.path.isfile(schema_json_path):
            raise FileNotFoundError(f"Schema file does not exist: {schema_json_path}")
        try:
            with open(schema_json_path, 'r') as f:
                schema = json.load(f)
            if not isinstance(schema, dict):
                raise ValueError("Schema JSON must be a dictionary.")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")

    try:
        db.create_collection(collection_name, **schema)
        print(f"Collection '{collection_name}' created successfully.")
    except CollectionInvalid as e:
        raise RuntimeError(f"Failed to create collection: {e}")


def main():
    db = get_mongo_db()
    ROOT_DIR = os.path.abspath(os.curdir)

    GAME_SCHEMA_JSON_PATH = os.path.join(ROOT_DIR, "src/db/mongodb/schema/games1.json")
    GAME_COLLECTION_NAME = "games"
    create_collection(db, GAME_COLLECTION_NAME, GAME_SCHEMA_JSON_PATH)

    # --- create indexes
    game_collection = db[GAME_COLLECTION_NAME]
    game_collection.create_index("game.ext_game_id", unique=True)

if __name__ == "__main__":
    main()
