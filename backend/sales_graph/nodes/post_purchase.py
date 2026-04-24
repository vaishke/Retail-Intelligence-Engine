"""
sales_graph/nodes/post_purchase.py

Wrapper node around agents/post_purchase_agent.py
"""

from datetime import datetime
from typing import Dict, Any

from bson import ObjectId
from bson.errors import InvalidId

from agents.post_purchase_agent import PostPurchaseAgent
from db.database import invoices_collection, orders_collection, shipments_collection


def _make_json_safe(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, dict):
        return {key: _make_json_safe(val) for key, val in value.items()}

    if isinstance(value, list):
        return [_make_json_safe(item) for item in value]

    return value


def _to_object_id(value: Any) -> ObjectId | None:
    if isinstance(value, ObjectId):
        return value

    try:
        return ObjectId(str(value))
    except (InvalidId, TypeError):
        return None


def post_purchase_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls PostPurchaseAgent for order confirmation, shipment, invoice, etc.
    
    READS from state:
    - loyalty_data (for order_id, final_amount)
    - payment_status (for transaction_id)
    - user_id
    - cart_items
    - delivery_address
    
    WRITES to state:
    - order_status (updated with shipment, invoice info)
    - last_worker
    - agent_call_history
    - last_error (if failure)
    """
    
    if state.get("current_intent") == "order_tracking":
        user_oid = _to_object_id(state.get("user_id"))
        if user_oid is None:
            return {
                "last_worker": "post_purchase_agent",
                "agent_call_history": state.get("agent_call_history", []) + ["post_purchase_agent"],
                "last_error": {
                    "code": "ORDER_LOOKUP_FAILED",
                    "message": "Invalid user id for order tracking",
                    "worker": "post_purchase_agent",
                    "retryable": False
                }
            }

        requested_order_id = state.get("intent_entities", {}).get("order_id")
        list_orders = bool(state.get("intent_entities", {}).get("list_orders"))
        latest_order_id = (state.get("order_status") or {}).get("order_id")

        if list_orders:
            recent_orders = []
            for order in orders_collection.find({"user_id": user_oid}).sort("created_at", -1).limit(5):
                order_id = order.get("_id")
                shipment = shipments_collection.find_one({"order_id": order_id})
                recent_orders.append(
                    {
                        "order_id": str(order_id),
                        "status": order.get("status"),
                        "created_at": _make_json_safe(order.get("created_at")),
                        "confirmed_at": _make_json_safe(order.get("confirmed_at")),
                        "final_amount": order.get("final_price", 0),
                        "tracking_number": shipment.get("tracking_number") if shipment else None,
                        "tracking_status": (shipment or {}).get("delivery_status") or "processing",
                        "items": _make_json_safe(order.get("items", [])),
                    }
                )

            if not recent_orders:
                return {
                    "last_worker": "post_purchase_agent",
                    "agent_call_history": state.get("agent_call_history", []) + ["post_purchase_agent"],
                    "last_error": {
                        "code": "NO_ORDERS_FOUND",
                        "message": "I couldn't find any recent orders yet",
                        "worker": "post_purchase_agent",
                        "retryable": False
                    }
                }

            return {
                "order_status": {
                    **(state.get("order_status") or {}),
                    "recent_orders": recent_orders,
                    "tracking_lookup": True,
                    "listing_orders": True,
                },
                "last_worker": "post_purchase_agent",
                "agent_call_history": state.get("agent_call_history", []) + ["post_purchase_agent"],
                "last_error": None
            }

        selected_order = None
        target_order_id = requested_order_id or latest_order_id

        if target_order_id:
            order_oid = _to_object_id(target_order_id)
            if order_oid is not None:
                selected_order = orders_collection.find_one({"_id": order_oid, "user_id": user_oid})

        if selected_order is None:
            selected_order = orders_collection.find_one(
                {"user_id": user_oid},
                sort=[("created_at", -1)]
            )

        if not selected_order:
            return {
                "last_worker": "post_purchase_agent",
                "agent_call_history": state.get("agent_call_history", []) + ["post_purchase_agent"],
                "last_error": {
                    "code": "NO_ORDERS_FOUND",
                    "message": "I couldn't find any orders to track yet",
                    "worker": "post_purchase_agent",
                    "retryable": False
                }
            }

        order_id = selected_order.get("_id")
        shipment = shipments_collection.find_one({"order_id": order_id})
        invoice = invoices_collection.find_one({"order_id": order_id})

        return {
            "order_status": {
                **(state.get("order_status") or {}),
                "order_id": str(order_id),
                "status": selected_order.get("status"),
                "created_at": _make_json_safe(selected_order.get("created_at")),
                "confirmed_at": _make_json_safe(selected_order.get("confirmed_at")),
                "final_amount": selected_order.get("final_price", 0),
                "payment": _make_json_safe(selected_order.get("payment", {})),
                "fulfillment": _make_json_safe(selected_order.get("fulfillment", {})),
                "items": _make_json_safe(selected_order.get("items", [])),
                "shipment_id": str(shipment.get("_id")) if shipment else None,
                "invoice_id": str(invoice.get("_id")) if invoice else None,
                "tracking_number": shipment.get("tracking_number") if shipment else None,
                "tracking_status": (shipment or {}).get("delivery_status") or "processing",
                "tracking_lookup": True,
                "requested_order_id": requested_order_id,
            },
            "last_worker": "post_purchase_agent",
            "agent_call_history": state.get("agent_call_history", []) + ["post_purchase_agent"],
            "last_error": None
        }

    loyalty_data = state.get("loyalty_data") or state.get("checkout_context") or {}
    payment_status = state.get("payment_status") or {}
    delivery_address = state.get("delivery_address")
    
    order_id = loyalty_data.get("order_id")
    transaction_id = payment_status.get("transaction_id")
    
    if not order_id or not transaction_id:
        return {
            "last_worker": "post_purchase_agent",
            "agent_call_history": state.get("agent_call_history", []) + ["post_purchase_agent"],
            "last_error": {
                "code": "MISSING_PREREQUISITES",
                "message": "Order ID and transaction ID required for post-purchase",
                "worker": "post_purchase_agent",
                "retryable": False
            }
        }
    
    # if not delivery_address or not delivery_address.get("city"):
    #     return {
    #         "last_worker": "post_purchase_agent",
    #         "agent_call_history": state.get("agent_call_history", []) + ["post_purchase_agent"],
    #         "last_error": {
    #             "code": "MISSING_ADDRESS",
    #             "message": "Delivery address with city is required",
    #             "worker": "post_purchase_agent",
    #             "retryable": False
    #         }
    #     }
    
    # If delivery_address is missing or has no city, build a default from location state
    if not delivery_address or not delivery_address.get("city"):
        location = state.get("location") or {}
        delivery_address = {
            "city": location.get("city", "Mumbai"),  # Default city fallback
            "line1": "",
            "line2": "",
            "state": "",
            "pincode": "",
            "country": "India"
        }
    
    try:
        # Build input for PostPurchaseAgent
        input_json = {
            "order_id": str(order_id),  # Convert ObjectId to string
            "transaction_id": transaction_id,
            "user_id": str(state["user_id"]),
            "session_id": state.get("session_id"),
            "cart_items": [
                {
                    "product_id": str(item["product_id"]),
                    "qty": item.get("qty", 1),
                    "price": item["price"]
                }
                for item in state.get("cart_items", [])
            ],
            "final_amount": loyalty_data.get("final_amount", 0),
            "delivery_address": delivery_address
        }
        
        # Call your existing post-purchase agent
        result = PostPurchaseAgent.handle_post_purchase(input_json)
        
        if result.get("success"):
            # Post-purchase steps completed successfully
            return {
                "cart_items": [],
                "loyalty_data": None,
                "checkout_context": None,
                "order_status": {
                    **(state.get("order_status") or {}),
                    "order_id": str(order_id),
                    "transaction_id": transaction_id,
                    "final_amount": loyalty_data.get("final_amount", 0),
                    "points_earned_at_checkout": loyalty_data.get("loyalty_points_earned", 0),
                    "confirmed": True,
                    "shipment_id": result.get("shipment_id"),
                    "invoice_id": result.get("invoice_id"),
                    "tracking_status": "processing",
                    "bonus_points": result.get("bonus_points", 0),
                    "loyalty_points_total": result.get("loyalty_points_total"),
                    "loyalty_tier": result.get("loyalty_tier"),
                    "cart_cleared": result.get("cart_cleared", False),
                },
                "checkout_stage": "completed",
                "payment_idempotency_key": None,
                "payment_method": None,
                "last_worker": "post_purchase_agent",
                "agent_call_history": state.get("agent_call_history", []) + ["post_purchase_agent"],
                "last_error": None
            }
        else:
            # Post-purchase processing failed
            return {
                "last_worker": "post_purchase_agent",
                "agent_call_history": state.get("agent_call_history", []) + ["post_purchase_agent"],
                "last_error": {
                    "code": "POST_PURCHASE_FAILED",
                    "message": result.get("message", "Post-purchase processing failed"),
                    "error_details": result.get("error"),
                    "worker": "post_purchase_agent",
                    "retryable": False  # Usually indicates data issue
                }
            }
    
    except Exception as e:
        # Unexpected exception
        return {
            "last_worker": "post_purchase_agent",
            "agent_call_history": state.get("agent_call_history", []) + ["post_purchase_agent"],
            "last_error": {
                "code": "EXCEPTION",
                "message": str(e),
                "worker": "post_purchase_agent",
                "retryable": True
            }
        }
