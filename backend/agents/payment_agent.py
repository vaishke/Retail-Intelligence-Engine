from db.database import orders_collection
from datetime import datetime
import uuid


class PaymentAgent:

    @staticmethod
    def process_payment(order_id: str, payment_method: str, details: dict = None):
        """
        Processes payment for an order.
        Updates the order's 'payment' sub-document on success.
        """

        # Fetch the order
        order = orders_collection.find_one({"_id": order_id})

        if not order:
            return {
                "success": False,
                "order_id": order_id,
                "message": "Order not found"
            }

        # Check if already paid
        if order.get("payment", {}).get("status") == "paid":
            return {
                "success": False,
                "order_id": order_id,
                "message": "Order already paid"
            }

        amount = order.get("final_price", 0)
        user_id = order.get("user_id")

        # Generate a transaction ID
        transaction_id = str(uuid.uuid4())

        # Simulate payment gateway success/failure
        success = True  # Change logic here if integrating real gateway

        payment_status = "paid" if success else "failed"

        # Update the order's payment sub-document
        orders_collection.update_one(
            {"_id": order_id},
            {"$set": {
                "payment.status": payment_status,
                "payment.method": payment_method,
                "payment.transaction_id": transaction_id,
                "payment.details": details or {},
                "payment.updated_at": datetime.utcnow()
            }}
        )

        return {
            "success": success,
            "order_id": order_id,
            "transaction_id": transaction_id,
            "amount": amount,
            "payment_method": payment_method,
            "message": "Payment successful" if success else "Payment failed"
        }