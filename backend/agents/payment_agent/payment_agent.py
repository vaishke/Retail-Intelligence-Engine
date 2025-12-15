from db.database import payments_collection, orders_collection
import datetime
import uuid


class PaymentAgent:

    def process_payment(self, order_id, payment_method, details=None):
        """
        Fetch order from DB → process payment → save payment record
        """

        # 1️⃣ Fetch order from DB
        order = orders_collection.find_one({"order_id": order_id})

        if not order:
            return {
                "success": False,
                "message": "Order not found"
            }

        if order.get("status") == "paid":
            return {
                "success": False,
                "message": "Order already paid"
            }

        amount = order["final_amount"]
        user_id = order["user_id"]

        # 2️⃣ Generate transaction ID
        transaction_id = str(uuid.uuid4())

        # 3️⃣ Simulate payment gateway
        success = True   # Replace later with Razorpay / Stripe / etc.

        # 4️⃣ Save payment record
        payment_record = {
            "transaction_id": transaction_id,
            "order_id": order_id,
            "user_id": user_id,
            "amount": amount,
            "payment_method": payment_method,
            "status": "success" if success else "failed",
            "created_at": datetime.datetime.utcnow()
        }

        payments_collection.insert_one(payment_record)

        # 5️⃣ Update order status
        if success:
            orders_collection.update_one(
                {"order_id": order_id},
                {"$set": {"status": "paid"}}
            )

        # 6️⃣ Return response
        return {
            "success": success,
            "transaction_id": transaction_id,
            "order_id": order_id,
            "amount": amount,
            "message": "Payment successful" if success else "Payment failed"
        }
