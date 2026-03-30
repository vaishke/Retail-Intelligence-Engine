"""
sales_graph/nodes/fulfilment.py

Wrapper node around agents/fulfillment_agent.py
"""

from typing import Dict, Any
from agents.fulfillment_agent import FulfillmentAgent
from bson import ObjectId
from db.database import orders_collection


def fulfilment_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls FulfillmentAgent to process order fulfillment.
    
    READS from state:
    - user_id
    - session_id
    - cart_items
    - loyalty_data (for order_id)
    - fulfillment_type (default: "SHIP_TO_HOME")
    - location (for store_location)
    
    WRITES to state:
    - order_status
    - last_worker
    - agent_call_history
    - last_error (if failure)
    """
    
    user_id = state.get("user_id")
    session_id = state.get("session_id")
    cart_items = state.get("cart_items", [])
    loyalty_data = state.get("loyalty_data", {})
    location = state.get("location", {})
    
    if not cart_items:
        return {
            "order_status": None,
            "last_worker": "fulfilment_agent",
            "agent_call_history": state.get("agent_call_history", []) + ["fulfilment_agent"],
            "last_error": {
                "code": "EMPTY_CART",
                "message": "Cannot fulfill empty order",
                "worker": "fulfilment_agent",
                "retryable": False
            }
        }
    
    try:
        # Format cart items with ObjectIds
        formatted_items = [
            {
                "product_id": ObjectId(item["product_id"]) if isinstance(item["product_id"], str) else item["product_id"],
                "qty": item.get("qty", 1),
                "price": item["price"]
            }
            for item in cart_items
        ]
        
        # Build order input for FulfillmentAgent
        order_input = {
            "user_id": ObjectId(user_id) if isinstance(user_id, str) else user_id,
            "session_id": ObjectId(session_id) if isinstance(session_id, str) else session_id,
            "items": formatted_items,
            "fulfillment_type": state.get("fulfillment_type", "SHIP_TO_HOME"),
            "store_location": location.get("store_id"),
            "order_id": loyalty_data.get("order_id"),  # Link to the order created by OfferLoyaltyAgent
            "final_price": loyalty_data.get("final_amount", 0),
            "discounts_applied": []  # Can be populated from loyalty_data if needed
        }
        
        # Call your existing fulfillment agent
        # NOTE: FulfillmentAgent.process_order() deducts stock correctly BUT also
        # inserts a NEW order document. We ignore that new order and instead update
        # the EXISTING order created by OfferLoyaltyAgent to avoid duplicates.
        result = FulfillmentAgent.process_order(order_input)

        # Normalize ObjectId fields to strings for state serialization
        if result.get("order_id") and not isinstance(result["order_id"], str):
            result["order_id"] = str(result["order_id"])
        if result.get("user_id") and not isinstance(result["user_id"], str):
            result["user_id"] = str(result["user_id"])

        # Update the EXISTING order (from OfferLoyaltyAgent) with fulfillment status
        existing_order_id = loyalty_data.get("order_id")
        if existing_order_id:
            orders_collection.update_one(
                {"_id": ObjectId(existing_order_id)},
                {"$set": {
                    "fulfillment.type": order_input["fulfillment_type"],
                    "fulfillment.status": result.get("status", "PENDING"),
                    "status": result.get("status", "PENDING").lower()
                }}
            )
            # Use the original order_id in result so downstream nodes are consistent
            result["order_id"] = existing_order_id

        if result.get("success"):
            # Fulfillment successful
            return {
                "order_status": result,
                "reservation_status": {
                    "reserved": True,
                    "store_id": location.get("store_id"),
                    "fulfillment_type": state.get("fulfillment_type", "SHIP_TO_HOME")
                },
                "last_worker": "fulfilment_agent",
                "agent_call_history": state.get("agent_call_history", []) + ["fulfilment_agent"],
                "last_error": None
            }
        else:
            # Fulfillment failed (partial or complete failure)
            return {
                "order_status": result,
                "last_worker": "fulfilment_agent",
                "agent_call_history": state.get("agent_call_history", []) + ["fulfilment_agent"],
                "last_error": {
                    "code": "FULFILMENT_FAILED",
                    "message": result.get("message", "Fulfillment failed"),
                    "worker": "fulfilment_agent",
                    "retryable": True  # Might be able to retry with different store
                }
            }
    
    except Exception as e:
        # Unexpected exception
        return {
            "order_status": None,
            "last_worker": "fulfilment_agent",
            "agent_call_history": state.get("agent_call_history", []) + ["fulfilment_agent"],
            "last_error": {
                "code": "EXCEPTION",
                "message": str(e),
                "worker": "fulfilment_agent",
                "retryable": True
            }
        }
