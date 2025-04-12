import json
import os

from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import PyMongoError, CollectionInvalid


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

def upsert_document(db: Database, collection_name: str, query: dict, new_values: dict) -> str:
    """
    Updates a document matching the query or inserts it if it doesn't exist.

    Parameters
    ----------
    db : pymongo.database.Database
        The MongoDB database object.
    collection_name : str
        Name of the collection.
    query : dict
        The filter query to find the document.
    new_values : dict
        The values to set (insert or update).

    Returns
    -------
    str
        The ID of the upserted document, or an empty string if only an update occurred.

    Raises
    ------
    ValueError
        If query or new_values is not a dictionary.
    RuntimeError
        If the upsert operation fails.
    """
    if not isinstance(query, dict) or not isinstance(new_values, dict):
        raise ValueError("Both query and new_values must be dictionaries.")

    try:
        collection: Collection = db[collection_name]
        result = collection.update_one(query, {"$set": new_values}, upsert=True)
        
        # Return inserted ID if a new doc was created, else empty string
        return str(result.upserted_id) if result.upserted_id else ""
    except PyMongoError as e:
        raise RuntimeError(f"Failed to upsert document in '{collection_name}': {e}")

