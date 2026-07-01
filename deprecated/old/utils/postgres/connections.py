import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

def get_postgres_connection() -> Connection:
    """
    Establishes and returns a connection to a PostgreSQL database using SQLAlchemy.

    Environment Variables
    ---------------------
    POSTGRES_USER : str
    POSTGRES_PASSWORD : str
    POSTGRES_DB : str
    POSTGRES_HOST : str
    POSTGRES_PORT : str

    Returns
    -------
    Connection
        A SQLAlchemy Connection object

    Raises
    ------
    FileNotFoundError
        If the .env file could not be found or loaded
    ValueError
        If any required environment variable is missing
    ConnectionError
        If the connection to PostgreSQL fails
    """
    if not load_dotenv():
        raise FileNotFoundError(".env file is missing. Please check!")

    required_vars = ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "POSTGRES_HOST", "POSTGRES_PORT"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db = os.getenv("POSTGRES_DB")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")

    try:
        engine = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{db}")
        connection = engine.connect()
    except Exception as e:
        raise ConnectionError(f"Error connecting to the postgres database: {e}")

    return connection
