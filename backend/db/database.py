# database.py
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

if not MONGO_URI or not DB_NAME:
    raise Exception("MONGO_URI or DB_NAME not loaded. Check .env file.")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Collections
users_collection = db["users"]
sessions_collection = db["sessions"]
products_collection = db["products"]
inventory_collection = db["inventory"]
orders_collection = db["orders"]
offers_collection = db["offers"]
shipments_collection = db["shipments"]
feedback_collection = db["feedback"]
invoices_collection = db["invoices"]
notifications_collection = db["notifications"]