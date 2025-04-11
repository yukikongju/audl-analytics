from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

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

