from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def reset_database():
    collections = db.list_collection_names()

    if not collections:
        print(f"No collections found in database '{DB_NAME}'. Nothing to clear.")
        return

    for col in collections:
        db[col].delete_many({})
        print(f"Cleared all documents in collection: {col}")

    print(f"\n✅ All collections in '{DB_NAME}' have been cleared successfully!")

if __name__ == "__main__":
    reset_database()
