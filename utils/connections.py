import os
import logging

from dotenv import load_dotenv
from sqlalchemy import create_engine

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


