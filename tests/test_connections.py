import pytest
from src.utils.mongodb.connections import get_mongo_db


def test_get_mongo_db():
    db = get_mongo_db()

