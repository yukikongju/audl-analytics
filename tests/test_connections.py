import pytest
from src.utils.mongodb.connections import get_mongo_db, get_mongo_collection


def test_get_mongo_db():
    db = get_mongo_db()

def test_existing_connection():
    collection = get_mongo_collection('game-events')

def test_uncreated_connection():
    with pytest.raises(ValueError):
        collection = get_mongo_collection('dummy')


