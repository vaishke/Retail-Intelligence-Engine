from db.database import inventory_collection, orders_collection, shipments_collection, invoices_collection, notifications_collection
from bson import ObjectId
from datetime import datetime

class PostPurchaseAgent:

    @staticmethod
    def confirm_order(order_id, transaction_id):
        order = orders_collection.find_one({"_id": ObjectId(order_id)})
        if not order:
            raise ValueError("Order not found")

        if order.get("status") == "confirmed":
            return {
                "order_id": str(order["_id"]),
                "status": "already_confirmed",
                "message": "Order was already confirmed"
            }

        orders_collection.update_one(
            {"_id": ObjectId(order_id)},
            {
                "$set": {
                    "status": "confirmed",
                    "payment.transaction_id": transaction_id,
                    "payment.status": "paid",
                    "payment.updated_at": datetime.utcnow(),
                    "confirmed_at": datetime.utcnow()
                }
            }
        )

        return {
            "order_id": str(order["_id"]),
            "status": "confirmed",
            "message": "Order confirmed successfully"
        }

    @staticmethod
    def reduce_inventory(delivery_city, cart_items):
        for item in cart_items:
            product_id = ObjectId(item["product_id"])
            quantity_needed = item["qty"]

            record = inventory_collection.find_one({"product_id": product_id})
            if not record:
                raise Exception(f"Inventory record not found for product_id {product_id}")

            # Use store_id mapping to city stocks (assuming schema has store_id mapped by city)
            store_stock = record.get("store_id_stock", {})  # adjust based on your actual inventory schema
            online_stock = record.get("quantity", 0)

            city_stock = store_stock.get(delivery_city, 0)

            if city_stock >= quantity_needed:
                inventory_collection.update_one(
                    {"product_id": product_id},
                    {"$inc": {f"store_id_stock.{delivery_city}": -quantity_needed}}
                )
            elif city_stock > 0 and (city_stock + online_stock) >= quantity_needed:
                remaining = quantity_needed - city_stock
                inventory_collection.update_one(
                    {"product_id": product_id},
                    {
                        "$set": {f"store_id_stock.{delivery_city}": 0},
                        "$inc": {"quantity": -remaining}
                    }
                )
            elif online_stock >= quantity_needed:
                inventory_collection.update_one(
                    {"product_id": product_id},
                    {"$inc": {"quantity": -quantity_needed}}
                )
            else:
                raise Exception(f"Insufficient stock for product_id {product_id}")

        return {"success": True, "message": "Inventory successfully updated"}

    @staticmethod
    def create_shipment(order_id, user_id, delivery_address, shipment_type="standard", carrier="TBD", tracking_number=None):
        shipment = {
            "order_id": ObjectId(order_id),
            "user_id": ObjectId(user_id),
            "shipment_type": shipment_type,
            "carrier": carrier,
            "tracking_number": tracking_number or f"TRK-{ObjectId()}",
            "delivery_status": "processing",
            "delivery_address": delivery_address,
            "assigned_agent": None,
            "expected_delivery_date": None,
            "actual_delivery_date": None,
            "last_updated": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }

        shipment_id = shipments_collection.insert_one(shipment).inserted_id
        return {"shipment_id": str(shipment_id), "status": "processing"}

    @staticmethod
    def generate_invoice(order_id, cart_items, final_amount):
        invoice = {
            "order_id": ObjectId(order_id),
            "items": [
                {
                    "product_id": ObjectId(item["product_id"]),
                    "qty": item["qty"],
                    "price": item["price"]
                } for item in cart_items
            ],
            "final_amount": final_amount,
            "issued_at": datetime.utcnow()
        }

        invoice_id = invoices_collection.insert_one(invoice).inserted_id
        return {"invoice_id": str(invoice_id), "amount": final_amount}

    @staticmethod
    def send_notification(user_id, order_id):
        notification = {
            "user_id": ObjectId(user_id),
            "type": "ORDER_CONFIRMED",
            "message": f"Your order {order_id} has been successfully placed.",
            "read": False,
            "created_at": datetime.utcnow()
        }

        notifications_collection.insert_one(notification)
        return {"success": True, "message": "Notification sent"}

    @staticmethod
    def handle_post_purchase(input_json):
        required_fields = ["order_id", "transaction_id", "user_id", "cart_items", "final_amount", "delivery_address"]
        for field in required_fields:
            if field not in input_json or input_json[field] is None:
                return {"success": False, "message": f"Missing required field: {field}"}

        delivery_address = input_json["delivery_address"]
        if not isinstance(delivery_address, dict) or not delivery_address.get("city"):
            return {"success": False, "message": "delivery_address.city is required"}

        cart_items = input_json["cart_items"]
        if not isinstance(cart_items, list) or len(cart_items) == 0:
            return {"success": False, "message": "cart_items must be a non-empty list"}

        for item in cart_items:
            if not all(k in item for k in ("product_id", "qty", "price")):
                return {"success": False, "message": "Each cart item must have product_id, qty, and price"}
            if item["qty"] <= 0:
                return {"success": False, "message": f"Invalid quantity for product_id {item.get('product_id')}"}

        try:
            PostPurchaseAgent.confirm_order(input_json["order_id"], input_json["transaction_id"])
            PostPurchaseAgent.reduce_inventory(delivery_address["city"], cart_items)
            shipment_json = PostPurchaseAgent.create_shipment(
                input_json["order_id"],
                input_json["user_id"],
                delivery_address
            )
            invoice_json = PostPurchaseAgent.generate_invoice(
                input_json["order_id"],
                cart_items,
                input_json["final_amount"]
            )
            PostPurchaseAgent.send_notification(input_json["user_id"], input_json["order_id"])

            return {
                "success": True,
                "order_id": input_json["order_id"],
                "shipment_id": shipment_json.get("shipment_id"),
                "invoice_id": invoice_json.get("invoice_id"),
                "message": "Order confirmed and post-purchase steps completed"
            }

        except Exception as e:
            return {"success": False, "message": "Post-purchase processing failed", "error": str(e)}