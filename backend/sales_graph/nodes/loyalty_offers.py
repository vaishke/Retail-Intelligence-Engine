"""
sales_graph/nodes/loyalty_offers.py

Wrapper node around agents/offer_loyalty_agent.py
"""

from typing import Dict, Any
from agents.offer_loyalty_agent import OfferLoyaltyAgent
from bson import ObjectId


def loyalty_offers_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls OfferLoyaltyAgent and updates state with loyalty/pricing data.
    
    READS from state:
    - user_id
    - cart_items
    - coupon_code (optional)
    - use_points (optional)
    
    WRITES to state:
    - loyalty_data
    - last_worker
    - agent_call_history
    - last_error (if failure)
    """
    
    user_id = state.get("user_id")
    cart_items = state.get("cart_items", [])
    coupon_code = state.get("coupon_code")
    use_points = state.get("use_points", 0)
    
    if not cart_items:
        return {
            "loyalty_data": None,
            "last_worker": "loyalty_offers_agent",
            "agent_call_history": state.get("agent_call_history", []) + ["loyalty_offers_agent"],
            "last_error": {
                "code": "EMPTY_CART",
                "message": "Cannot process loyalty for empty cart",
                "worker": "loyalty_offers_agent",
                "retryable": False
            }
        }
    
    try:
        # Format cart items with ObjectIds for MongoDB
        formatted_cart = [
            {
                "product_id": ObjectId(item["product_id"]) if isinstance(item["product_id"], str) else item["product_id"],
                "qty": item.get("qty", 1),
                "price": item["price"]
            }
            for item in cart_items
        ]
        
        # Call your existing loyalty agent
        loyalty_agent = OfferLoyaltyAgent()
        result = loyalty_agent.process_checkout(
            user_id=ObjectId(user_id) if isinstance(user_id, str) else user_id,
            cart_items=formatted_cart,
            coupon_code=coupon_code,
            use_points=use_points
        )
        
        if result.get("success"):
            # Success path
            return {
                "loyalty_data": result,
                "checkout_context": result,
                "last_worker": "loyalty_offers_agent",
                "agent_call_history": state.get("agent_call_history", []) + ["loyalty_offers_agent"],
                "last_error": None
            }
        else:
            # Agent returned error
            return {
                "loyalty_data": None,
                "last_worker": "loyalty_offers_agent",
                "agent_call_history": state.get("agent_call_history", []) + ["loyalty_offers_agent"],
                "last_error": {
                    "code": "LOYALTY_FAILED",
                    "message": result.get("message", "Loyalty processing failed"),
                    "worker": "loyalty_offers_agent",
                    "retryable": False
                }
            }
    
    except Exception as e:
        # Unexpected exception
        return {
            "loyalty_data": None,
            "last_worker": "loyalty_offers_agent",
            "agent_call_history": state.get("agent_call_history", []) + ["loyalty_offers_agent"],
            "last_error": {
                "code": "EXCEPTION",
                "message": str(e),
                "worker": "loyalty_offers_agent",
                "retryable": True  # Might be a temporary DB issue
            }
        }
