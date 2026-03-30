"""
sales_graph/nodes/post_purchase.py

Wrapper node around agents/post_purchase_agent.py
"""

from typing import Dict, Any
from agents.post_purchase_agent import PostPurchaseAgent


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
    
    loyalty_data = state.get("loyalty_data", {})
    payment_status = state.get("payment_status", {})
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
                "order_status": {
                    **state.get("order_status", {}),
                    "confirmed": True,
                    "shipment_id": result.get("shipment_id"),
                    "invoice_id": result.get("invoice_id"),
                    "tracking_status": "processing"
                },
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
