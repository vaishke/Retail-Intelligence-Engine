import random

from db.database import inventory_collection, orders_collection, shipments_collection, invoices_collection, notifications_collection, users_collection
from bson import ObjectId
from datetime import datetime
from services.cart_service import CartService

class PostPurchaseAgent:
    BONUS_POINTS_RANGE = (10, 50)
    TIER_THRESHOLDS = {
        "Bronze": 0,
        "Silver": 500,
        "Gold": 5000,
        "Platinum": 15000,
    }

    @staticmethod
    def calculate_tier(total_points):
        if total_points >= PostPurchaseAgent.TIER_THRESHOLDS["Platinum"]:
            return "Platinum"
        if total_points >= PostPurchaseAgent.TIER_THRESHOLDS["Gold"]:
            return "Gold"
        if total_points >= PostPurchaseAgent.TIER_THRESHOLDS["Silver"]:
            return "Silver"
        return "Bronze"

    @staticmethod
    def confirm_order(order_id, transaction_id):
        order = orders_collection.find_one({"_id": ObjectId(order_id)})
        if not order:
            raise ValueError("Order not found")

        if order.get("status") == "confirmed":
            return {
                "order_id": str(order["_id"]),
                "status": "already_confirmed",
                "message": "Order was already confirmed",
                "bonus_points": order.get("loyalty_bonus_points", 0)
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
    def award_bonus_loyalty_points(user_id, order_id):
        user_oid = ObjectId(user_id)
        order_oid = ObjectId(order_id)

        order = orders_collection.find_one({"_id": order_oid}, {"loyalty_bonus_points": 1})
        if not order:
            raise ValueError("Order not found while awarding loyalty points")

        existing_bonus = order.get("loyalty_bonus_points")
        if existing_bonus is not None:
            user = users_collection.find_one({"_id": user_oid}, {"loyalty": 1}) or {}
            total_points = user.get("loyalty", {}).get("points", 0)
            return {
                "bonus_points": existing_bonus,
                "new_total_points": total_points,
                "tier": user.get("loyalty", {}).get("tier", "Bronze"),
                "already_awarded": True,
            }

        bonus_points = random.randint(*PostPurchaseAgent.BONUS_POINTS_RANGE)

        user = users_collection.find_one({"_id": user_oid}, {"loyalty": 1, "past_purchases": 1})
        if not user:
            raise ValueError("User not found while awarding loyalty points")

        current_points = user.get("loyalty", {}).get("points", 0)
        updated_points = current_points + bonus_points
        updated_tier = PostPurchaseAgent.calculate_tier(updated_points)

        users_collection.update_one(
            {"_id": user_oid},
            {
                "$inc": {"loyalty.points": bonus_points},
                "$set": {"loyalty.tier": updated_tier},
                "$addToSet": {"past_purchases": str(order_oid)},
            }
        )

        orders_collection.update_one(
            {"_id": order_oid},
            {"$set": {"loyalty_bonus_points": bonus_points}}
        )

        return {
            "bonus_points": bonus_points,
            "new_total_points": updated_points,
            "tier": updated_tier,
            "already_awarded": False,
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
            confirmation = PostPurchaseAgent.confirm_order(input_json["order_id"], input_json["transaction_id"])
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
            loyalty_bonus = PostPurchaseAgent.award_bonus_loyalty_points(
                input_json["user_id"],
                input_json["order_id"]
            )
            cart_clear_result = CartService.clear_cart(
                input_json["user_id"],
                input_json.get("session_id")
            )

            return {
                "success": True,
                "order_id": input_json["order_id"],
                "shipment_id": shipment_json.get("shipment_id"),
                "invoice_id": invoice_json.get("invoice_id"),
                "bonus_points": loyalty_bonus.get("bonus_points", 0),
                "loyalty_points_total": loyalty_bonus.get("new_total_points"),
                "loyalty_tier": loyalty_bonus.get("tier"),
                "cart_cleared": cart_clear_result.get("success", False),
                "message": "Order confirmed and post-purchase steps completed",
                "confirmation_status": confirmation.get("status"),
            }

        except Exception as e:
            return {"success": False, "message": "Post-purchase processing failed", "error": str(e)}
