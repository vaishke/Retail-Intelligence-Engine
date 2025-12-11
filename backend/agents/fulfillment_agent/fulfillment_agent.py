# fulfillment_agent.py
from backend.db.database import orders_collection, products_collection
import datetime

# --- Mock Inventory Agent ---
class InventoryAgentMock:
    def check_stock(self, sku, userLocation=None):
        # For testing, fetch from products_collection
        product = products_collection.find_one({"sku": sku})
        if not product:
            return 0  # product not found
        # Return store stock if location provided, else availableOnline
        if userLocation and userLocation in product.get("storeStock", {}):
            return product["storeStock"][userLocation]
        return product.get("availableOnline", 0)

# --- Mock Payment Agent ---
class PaymentAgentMock:
    def process_payment(self, user_id, amount):
        # For testing, always succeed
        return "success"

# --- Fulfillment Agent ---
class FulfillmentAgent:
    def __init__(self):
        self.inventory_agent = InventoryAgentMock()
        self.payment_agent = PaymentAgentMock()

    def process_order(self, order, userLocation=None):
        fulfilled = []
        unfulfilled = []

        for item in order["products"]:
            sku = item["sku"]
            qty = item["quantity"]
            available = self.inventory_agent.check_stock(sku, userLocation)

            if available >= qty:
                fulfilled.append(item)
            else:
                if available > 0:
                    fulfilled.append({"sku": sku, "quantity": available, "price": item["price"]})
                    unfulfilled.append({"sku": sku, "quantity": qty - available, "price": item["price"]})
                else:
                    unfulfilled.append(item)

        total_amount = sum([p["quantity"] * p["price"] for p in fulfilled])
        order["total_amount"] = total_amount

        # Process payment
        payment_status = self.payment_agent.process_payment(order["user_id"], total_amount)
        if payment_status != "success":
            return {
                "order_id": order["order_id"],
                "status": "payment_failed",
                "fulfilled_products": fulfilled,
                "unfulfilled_products": unfulfilled,
                "message": "Payment failed"
            }

        # Save order to MongoDB
        orders_collection.insert_one({
            "order_id": order["order_id"],
            "user_id": order["user_id"],
            "fulfilled_products": fulfilled,
            "unfulfilled_products": unfulfilled,
            "total_amount": total_amount,
            "status": "processed" if not unfulfilled else "partial",
            "timestamp": datetime.datetime.utcnow()
        })

        return {
            "order_id": order["order_id"],
            "status": "processed" if not unfulfilled else "partial",
            "fulfilled_products": fulfilled,
            "unfulfilled_products": unfulfilled,
            "message": "Order processed successfully"
        }

    def process_orders_batch(self, orders, userLocation=None):
        results = []
        for order in orders:
            result = self.process_order(order, userLocation)
            results.append(result)
        return results