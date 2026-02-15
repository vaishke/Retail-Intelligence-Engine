from pymongo import MongoClient
from dotenv import load_dotenv
import os

# loads .env from project root
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

if not MONGO_URI or not DB_NAME:
    raise Exception("MONGO_URI or DB_NAME not loaded. Check .env file.")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

products_collection = db["products"]
orders_collection = db["orders"]
payments_collection = db["payments"]
loyalty_collection = db["loyalty"]
users_collection = db["users"]
offers_collection = db["offers"]
inventory_collection = db["inventory"]
sessions_collection = db["sessions"]
shipments_collection = db["shipments"]
notifications_collection = db["notifications"]
invoices_collection = db["invoices"]