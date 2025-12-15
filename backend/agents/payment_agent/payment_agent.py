from backend.db.database import payments_collection
import datetime
import uuid

class PaymentAgent:
    def __init__(self):
        pass

    def process_payment(self, payment_request):
        """
        Expected input format:
        {
            "order_id": "ORD001",
            "user_id": "USER01",
            "amount": 5000,
            "payment_method": "card / wallet / upi",
            "details": { ... }  # card or UPI info
        }
        """

        # 🔹 Generate Transaction ID
        transaction_id = str(uuid.uuid4())

        # 🔹 Simulate payment processing (mock or real gateway)
        success = True  # Replace with real API logic later

        # 📝 Save record
        record = {
            "transaction_id": transaction_id,
            "order_id": payment_request["order_id"],
            "user_id": payment_request["user_id"],
            "amount": payment_request["amount"],
            "payment_method": payment_request["payment_method"],
            "status": "success" if success else "failed",
            "timestamp": datetime.datetime.utcnow()
        }
        payments_collection.insert_one(record)

        # ✅ Return response
        return {
            "transaction_id": transaction_id,
            "order_id": payment_request["order_id"],
            "status": "success" if success else "failed",
            "message": "Payment completed" if success else "Payment failed"
        }
