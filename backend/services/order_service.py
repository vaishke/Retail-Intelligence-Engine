from datetime import datetime
from typing import Any, Dict, List

from bson import ObjectId
from bson.errors import InvalidId

from agents.fulfillment_agent import FulfillmentAgent
from agents.offer_loyalty_agent import OfferLoyaltyAgent
from agents.payment_agent import PaymentAgent
from agents.post_purchase_agent import PostPurchaseAgent
from db.database import invoices_collection, orders_collection, shipments_collection


class OrderService:
    @staticmethod
    def list_orders_for_user(user_id: str) -> Dict[str, Any]:
        user_oid = OrderService._to_object_id(user_id)
        if user_oid is None:
            return {"success": False, "message": "Invalid user_id"}

        orders = list(
            orders_collection.find({"user_id": user_oid}).sort("created_at", -1)
        )

        serialized_orders = []
        for order in orders:
            order_id = order.get("_id")
            shipment = shipments_collection.find_one({"order_id": order_id})
            invoice = invoices_collection.find_one({"order_id": order_id})

            serialized_orders.append(
                {
                    "id": str(order_id),
                    "user_id": str(order.get("user_id")) if order.get("user_id") else None,
                    "status": order.get("status", "pending"),
                    "created_at": OrderService._make_json_safe(order.get("created_at")),
                    "confirmed_at": OrderService._make_json_safe(order.get("confirmed_at")),
                    "final_price": order.get("final_price", 0),
                    "payment": OrderService._make_json_safe(order.get("payment", {})),
                    "fulfillment": OrderService._make_json_safe(order.get("fulfillment", {})),
                    "items": OrderService._make_json_safe(order.get("items", [])),
                    "shipment_id": str(shipment["_id"]) if shipment else None,
                    "invoice_id": str(invoice["_id"]) if invoice else None,
                    "tracking_number": shipment.get("tracking_number") if shipment else None,
                    "delivery_status": shipment.get("delivery_status") if shipment else None,
                    "loyalty_bonus_points": order.get("loyalty_bonus_points", 0),
                }
            )

        return {"success": True, "orders": serialized_orders}

    @staticmethod
    def place_order(data: Dict[str, Any]) -> Dict[str, Any]:
        user_id = data.get("user_id")
        items = data.get("items", [])
        payment_method = data.get("payment_method", "CARD")
        coupon_code = data.get("coupon_code")
        use_points = data.get("use_points", 0)
        delivery_address = data.get("delivery_address") or {}

        if not user_id:
            return {"success": False, "message": "user_id is required"}

        if not isinstance(items, list) or not items:
            return {"success": False, "message": "items must be a non-empty list"}

        user_oid = OrderService._to_object_id(user_id)
        if user_oid is None:
            return {"success": False, "message": "Invalid user_id"}

        formatted_items = OrderService._format_items(items)
        if not formatted_items:
            return {"success": False, "message": "Valid order items are required"}

        loyalty_agent = OfferLoyaltyAgent()
        loyalty_result = loyalty_agent.process_checkout(
            user_id=user_oid,
            cart_items=formatted_items,
            coupon_code=coupon_code,
            use_points=use_points,
        )
        if not loyalty_result.get("success"):
            return loyalty_result

        order_id = loyalty_result.get("order_id")

        payment_result = PaymentAgent.process_payment(
            order_id=order_id,
            payment_method=payment_method,
            details=data.get("payment_details"),
        )
        if not payment_result.get("success"):
            return {
                "success": False,
                "stage": "payment",
                "order_id": order_id,
                "message": payment_result.get("message", "Payment failed"),
                "payment": OrderService._make_json_safe(payment_result),
            }

        fulfillment_result = FulfillmentAgent.process_order(
            {
                "user_id": user_oid,
                "session_id": None,
                "items": formatted_items,
                "fulfillment_type": data.get("fulfillment_type", "SHIP_TO_HOME"),
                "store_location": data.get("store_location"),
                "order_id": order_id,
                "final_price": loyalty_result.get("final_amount", 0),
                "discounts_applied": [],
                "payment": {
                    "status": "paid",
                    "method": payment_result.get("payment_method"),
                    "transaction_id": payment_result.get("transaction_id"),
                    "updated_at": datetime.utcnow(),
                },
            }
        )
        if not fulfillment_result.get("success"):
            return {
                "success": False,
                "stage": "fulfillment",
                "order_id": order_id,
                "message": fulfillment_result.get("message", "Fulfillment failed"),
                "fulfillment": OrderService._make_json_safe(fulfillment_result),
            }

        normalized_address = {
            "line1": delivery_address.get("line1", ""),
            "line2": delivery_address.get("line2", ""),
            "city": delivery_address.get("city", "Mumbai"),
            "state": delivery_address.get("state", ""),
            "pincode": delivery_address.get("pincode", ""),
            "country": delivery_address.get("country", "India"),
        }

        post_purchase_result = PostPurchaseAgent.handle_post_purchase(
            {
                "order_id": order_id,
                "transaction_id": payment_result.get("transaction_id"),
                "user_id": str(user_oid),
                "session_id": data.get("session_id"),
                "cart_items": [
                    {
                        "product_id": str(item["product_id"]),
                        "qty": item["qty"],
                        "price": item["price"],
                    }
                    for item in formatted_items
                ],
                "final_amount": loyalty_result.get("final_amount", 0),
                "delivery_address": normalized_address,
            }
        )
        if not post_purchase_result.get("success"):
            return {
                "success": False,
                "stage": "post_purchase",
                "order_id": order_id,
                "message": post_purchase_result.get("message", "Post-purchase failed"),
                "post_purchase": OrderService._make_json_safe(post_purchase_result),
            }

        return {
            "success": True,
            "order_id": order_id,
            "payment": OrderService._make_json_safe(payment_result),
            "fulfillment": OrderService._make_json_safe(fulfillment_result),
            "post_purchase": OrderService._make_json_safe(post_purchase_result),
            "loyalty": {
                "points_earned_at_checkout": loyalty_result.get("loyalty_points_earned", 0),
                "bonus_points": post_purchase_result.get("bonus_points", 0),
                "total_points": post_purchase_result.get("loyalty_points_total"),
                "tier": post_purchase_result.get("loyalty_tier"),
            },
            "message": "Order placed successfully",
        }

    @staticmethod
    def _to_object_id(value: Any) -> ObjectId | None:
        if isinstance(value, ObjectId):
            return value
        try:
            return ObjectId(str(value))
        except (InvalidId, TypeError):
            return None

    @staticmethod
    def _format_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        formatted: List[Dict[str, Any]] = []
        for item in items:
            product_oid = OrderService._to_object_id(item.get("product_id"))
            qty = item.get("qty", item.get("quantity", 1))
            price = item.get("price", 0)

            if product_oid is None or not qty or qty <= 0:
                continue

            formatted.append(
                {
                    "product_id": product_oid,
                    "qty": int(qty),
                    "price": float(price),
                }
            )

        return formatted

    @staticmethod
    def _make_json_safe(value: Any) -> Any:
        if isinstance(value, ObjectId):
            return str(value)

        if isinstance(value, datetime):
            return value.isoformat()

        if isinstance(value, dict):
            return {
                key: OrderService._make_json_safe(val)
                for key, val in value.items()
            }

        if isinstance(value, list):
            return [OrderService._make_json_safe(item) for item in value]

        return value
