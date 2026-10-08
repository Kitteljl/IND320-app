"""MongoDB connection, shared by the notebook and the Streamlit app."""

from pymongo import MongoClient

from config import get_secret

DB_NAME = "ind320"


def get_mongo_client() -> MongoClient:
    return MongoClient(get_secret("mongo", "uri"), serverSelectionTimeoutMS=8000)


def get_mongo_db():
    return get_mongo_client()[DB_NAME]


def check_mongo() -> bool:
    """Ping the cluster. Returns True if the connection and login work."""
    get_mongo_client().admin.command("ping")
    return True