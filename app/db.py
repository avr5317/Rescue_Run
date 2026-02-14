import os
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, DESCENDING

# Load variables from .env (project root)
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "mutual_aid")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI is not set. Add it to your .env file.")

# Optional: add server selection timeout so failures show fast
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=8000)

db = client[DB_NAME]

requests_col = db["requests"]
donations_col = db["donations"]

def ensure_indexes():
    # Requests
    requests_col.create_index([("status", ASCENDING)])
    requests_col.create_index([("rank_score", DESCENDING)])
    requests_col.create_index([("location.lat", ASCENDING), ("location.lng", ASCENDING)])

    # Donations
    donations_col.create_index([("request_id", ASCENDING), ("created_at", DESCENDING)])

ensure_indexes()
