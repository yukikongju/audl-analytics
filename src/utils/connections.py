import os
import logging

from dotenv import load_dotenv
from sqlalchemy import create_engine
from pymongo import MongoClient
from pymongo.database import Database

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

def get_postgres_connection():
    load_dotenv()

    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db = os.getenv("POSTGRES_DB")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")

    try:
        engine = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{db}")
        connection = engine.connect()
    except Exception as e:
        logging.error(f"Error connecting to the postgres database: {e}")
        return

    return connection

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
        client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
    except Exception as e:
        raise ConnectionError(f"failed to connect to MongoDB: {e}")

    # --- check if database exists
    if mongo_db not in client.list_database_names():
        raise ValueError(f"Mongo database {mongo_db} doesn't exists. Please check!")

    return client[mongo_db]

