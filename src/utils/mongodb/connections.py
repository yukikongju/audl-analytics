import certifi
import os

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database

import ssl
ssl._create_default_https_context = ssl._create_unverified_context


def get_mongo_db() -> Database:
    """
    Establishes and returns a MongoDB database connection using environment variables.

    Environment Variables
    ---------------------
    ME_CONFIG_MONGODB_URL : str
        MongoDB connection string (e.g., "mongodb://localhost:27017")
    MONGO_DB_NAME : str, optional
        Name of the database to connect to (defaults to "audl" if not set)

    Returns
    -------
    Database
        A pymongo Database instance

    Raises
    ------
    ValueError
        If the connection URL is missing or invalid
    """
    # --- check if .env file is missing
    if not load_dotenv():
        raise FileNotFoundError(".env file is missing. Please check!")

    # --- check if environment variables are missing
    mongo_url = os.getenv("ME_CONFIG_MONGODB_URL")
    mongo_db = os.getenv("MONGO_DB_NAME")
    if not mongo_url:
        raise ValueError("Please define the environment variable ME_CONFIG_MONGODB_URL")
    if not mongo_db:
        raise ValueError("Please define the environment variable MONGO_DB_NAME")

    # --- connect to database
    try: 
        client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where())
        client.admin.command("ping")
    except Exception as e:
        raise ConnectionError(f"failed to connect to MongoDB: {e}")

    # --- check if database exists
    if mongo_db not in client.list_database_names():
        raise ValueError(f"Mongo database {mongo_db} doesn't exists. Please check!")

    return client[mongo_db]

def get_mongo_collection(collection_name: str):
    """
    Returns MongoDB collection

    Params
    ------
    collection_name: str
        name of the collection

    Raises
    ------
    ValueError
        if collection doesn't exist in database name
    ConnectionError
    """
    db = get_mongo_db()

    if collection_name not in db.list_collection_names():
        raise ValueError(f"The collection {collection_name} doesn't exist in the database. Please check!")

    try:
        collection = db[collection_name]
    except:
        raise ConnectionError(f"An error has occured when connecting to the collection {collection_name}.")

    return collection

