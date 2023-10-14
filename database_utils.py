from decouple import config
from pymongo import MongoClient
from neo4j import GraphDatabase


def load_mongodb_client():
    # read secrets credentials from .env
    USERNAME = config('MONGODB_USERNAME')
    PASSWORD = config('MONGODB_PASSWORD')
    HOST = config('MONGODB_HOST')
    PORT = config('MONGODB_PORT')
    DATABASE_NAME = config('MONGODB_DATABASE_NAME')

    # connect to mongodb
    client = MongoClient(f"mongodb://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DATABASE_NAME}")
    return client

def load_neo4j_client():
    # read secrets credentials from .env
    USERNAME = config('NEO4J_USERNAME')
    PASSWORD = config('NEO4J_PASSWORD')
    URI = config('NEO4J_URI')

    # connect to neo4j
    client = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
    return client

