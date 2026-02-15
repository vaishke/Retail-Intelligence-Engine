from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "Retail_Intelligence_Agent")  # default if env missing
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
orders_collection = db.orders
users_collection = db.users

class PaymentAgent:
    @staticmethod
    def process_payment(order_id, payment_method=None, details=None):
        # Fetch order
        order = orders_collection.find_one({"_id": ObjectId(order_id)})
        if not order:
            return {"success": False, "message": "Order not found"}

        if order["payment"]["status"] == "success":
            return {"success": False, "message": "Order already paid"}

        # Simulate payment (mostly succeed)
        success = True

        # Generate transaction ID
        transaction_id = str(uuid.uuid4()) if success else None

        # Update order payment
        orders_collection.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {
                "payment.status": "success" if success else "failed",
                "payment.method": payment_method if payment_method else "test_card",
                "payment.transaction_id": transaction_id,
                "payment.updated_at": datetime.datetime.utcnow()
            }}
        )

        return {
            "success": success,
            "order_id": order_id,
            "transaction_id": transaction_id,
            "amount": order["final_price"],
            "payment_method": payment_method,
            "message": "Payment successful" if success else "Payment failed"
        }

# --- TEST RUN ---
order_id = "6991a59d9f79e537a7628ca0"  # pending payment
result = PaymentAgent.process_payment(order_id, payment_method="card", details={"card_last4": "4321"})
print(result)

# Optional: check updated order
updated_order = orders_collection.find_one({"_id": ObjectId(order_id)})
print(updated_order)