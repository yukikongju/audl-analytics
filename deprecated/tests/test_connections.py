import pytest
from src.utils.mongodb.connections import get_mongo_db, get_mongo_collection, get_mongo_document


def test_get_mongo_db():
    db = get_mongo_db()

def test_existing_connection():
    collection = get_mongo_collection('game-events')

def test_nonexistant_connection():
    with pytest.raises(ValueError):
        collection = get_mongo_collection('dummy')

def test_existing_document():
    query = {"game.ext_game_id":  '2024-08-24-CAR-MIN'}
    doc = get_mongo_document('game-events', query)

def test_missing_document():
    query = {"game.ext_game_id":  '2024-08-24-CAR-MEN'}
    with pytest.raises(ValueError):
        doc = get_mongo_document('game-events', query)

