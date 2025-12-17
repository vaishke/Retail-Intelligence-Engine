from db.database import payments_collection, orders_collection
import datetime
import uuid


class PaymentAgent:

    @staticmethod
    def process_payment(order_id, payment_method, details=None):
        # Fetch order
        order = orders_collection.find_one({"order_id": order_id})

        if not order:
            return {
                "success": False,
                "order_id": order_id,
                "message": "Order not found"
            }

        if order.get("status") == "paid":
            return {
                "success": False,
                "order_id": order_id,
                "message": "Order already paid"
            }

        amount = order["final_amount"]
        user_id = order["user_id"]

        # Generate transaction ID
        transaction_id = str(uuid.uuid4())

        # Simulate payment gateway (replace with real gateway logic)
        success = True  # or False if failure simulation

        # Save payment record
        payment_record = {
            "transaction_id": transaction_id,
            "order_id": order_id,
            "user_id": user_id,
            "amount": amount,
            "payment_method": payment_method,
            "status": "success" if success else "failed",
            "details": details or {},
            "created_at": datetime.datetime.utcnow()
        }
        payments_collection.insert_one(payment_record)

        # Update order status if payment succeeded
        if success:
            orders_collection.update_one(
                {"order_id": order_id},
                {"$set": {"status": "paid"}}
            )

        return {
            "success": success,
            "order_id": order_id,
            "transaction_id": transaction_id,
            "amount": amount,
            "payment_method": payment_method,
            "message": "Payment successful" if success else "Payment failed"
        }
