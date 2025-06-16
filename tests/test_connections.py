import pytest
from src.utils.mongodb.connections import get_mongo_db, get_mongo_collection


def test_get_mongo_db():
    db = get_mongo_db()

def test_get_mongo_connections():
    collection = get_mongo_collection('game-events')



