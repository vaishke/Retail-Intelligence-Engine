from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db["orders"]
collection.insert_one({
    "order_id": "ORD123",
    "user_id": "USER01",
    "cart_items": [
        {"sku": "SHOE001", "price": 3000, "quantity": 2},
        {"sku": "TSHIRT001", "price": 1500, "quantity": 1}
    ],
    "final_amount": 7500,
    "status": "paid",
    "created_at": datetime.utcnow()
})

# test_data = [
#     {
#         "sku": "SHOE001",
#         "productName": "Nike Air Zoom",
#         "category": "Footwear",
#         "price": 2999,
#         "availableOnline": 5,
#         "storeStock": {"Hyderabad": 2, "Bangalore": 1}
#     },
#     {
#         "sku": "SHOE002",
#         "productName": "Adidas Runner",
#         "category": "Footwear",
#         "price": 2499,
#         "availableOnline": 0,
#         "storeStock": {"Hyderabad": 0, "Bangalore": 0}
#     },
#     {
#         "sku": "SHOE003",
#         "productName": "Puma Flex",
#         "category": "Footwear",
#         "price": 1999,
#         "availableOnline": 3,
#         "storeStock": {"Hyderabad": 0, "Bangalore": 4}
#     },
#     {
#         "sku": "TSHIRT001",
#         "productName": "Cotton T-Shirt",
#         "category": "Clothing",
#         "price": 999,
#         "availableOnline": 10,
#         "storeStock": {"Hyderabad": 3}
#     },
#     {
#         "sku": "TSHIRT002",
#         "productName": "Oversized Tee",
#         "category": "Clothing",
#         "price": 1499,
#         "storeStock": {"Hyderabad": 0, "Bangalore": 0},
#         "availableOnline": 0
#     }
# ]

# collection.insert_many(test_data)
# print("Test data inserted successfully!")
