"""
sales_graph/nodes/response_generator.py

Formats state into user-facing responses.
Uses templates, not LLM (for speed and cost efficiency).
"""

from typing import Dict, Any


def response_generator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates the final response based on confirmation_context.
    
    READS from state:
    - confirmation_context
    - All relevant data fields
    
    WRITES to state:
    - response (the final output to user)
    """
    
    context = state.get("confirmation_context")
    
    if context == "order_summary":
        response = format_order_summary(state)
    elif context == "reservation_summary":
        response = format_reservation_summary(state)
    elif context == "payment_retry":
        response = format_payment_retry(state)
    elif context == "empty_cart":
        response = {"message": "Your cart is empty. Would you like some recommendations?"}
    elif context == "no_items_to_check":
        response = {"message": "Please add items to your cart or get recommendations first."}
    elif context == "error_response":
        response = format_error_response(state)
    elif context == "max_chains_reached":
        response = {"message": "Processing... Please wait while I gather information for you."}
    else:
        # Default response based on last worker
        response = format_default_response(state)
    
    return {"response": response}


def format_order_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formats checkout confirmation with order summary.
    """
    loyalty_data = state.get("loyalty_data", {})
    cart_items = state.get("cart_items", [])
    
    return {
        "message": "Here's your order summary:",
        "data": {
            "items": cart_items,
            "cart_total": loyalty_data.get("cart_total", 0),
            "discount": loyalty_data.get("coupon_discount", 0),
            "points_used": loyalty_data.get("loyalty_points_used", 0),
            "final_amount": loyalty_data.get("final_amount", 0),
            "points_earned": loyalty_data.get("loyalty_points_earned", 0),
            "new_tier": loyalty_data.get("new_tier")
        },
        "prompt": "Would you like to proceed with payment?"
    }


def format_reservation_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formats reservation confirmation.
    """
    inventory_status = state.get("inventory_status", {})
    cart_items = state.get("cart_items", [])
    location = state.get("location", {})
    
    return {
        "message": f"Your items are available at store {location.get('store_id', 'near you')}.",
        "data": {
            "items": cart_items,
            "store_location": location
        },
        "prompt": "Shall I reserve these items for you?"
    }


def format_payment_retry(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formats payment retry message.
    """
    payment_status = state.get("payment_status", {})
    
    return {
        "message": f"Payment failed: {payment_status.get('message', 'Unknown error')}",
        "prompt": "Would you like to retry or try a different payment method?"
    }


def format_error_response(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formats generic error response.
    """
    error = state.get("last_error", {})
    
    return {
        "message": f"Sorry, something went wrong: {error.get('message', 'Unknown error')}",
        "prompt": "Please try again or let me know if you need help with something else."
    }


def format_default_response(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Default response based on last completed worker.
    """
    last_worker = state.get("last_worker")
    
    if last_worker == "recommendation_agent":
        recommended_items = state.get("recommended_items", [])
        return {
            "message": f"I found {len(recommended_items)} products for you:",
            "data": {"recommendations": recommended_items},
            "prompt": "Would you like to add any to your cart or check availability?"
        }
    
    elif last_worker == "inventory_agent":
        inventory_verified = state.get("inventory_verified", False)
        if inventory_verified:
            return {
                "message": "Great news! All items are in stock.",
                "prompt": "Would you like to proceed to checkout?"
            }
        else:
            return {
                "message": "Some items are out of stock. Let me suggest alternatives.",
                "prompt": None
            }
    
    elif last_worker == "loyalty_offers_agent":
        loyalty_data = state.get("loyalty_data", {})
        return {
            "message": f"Your current loyalty tier: {loyalty_data.get('new_tier', 'Silver')}",
            "data": {
                "points": loyalty_data.get("loyalty_points_earned", 0),
                "tier": loyalty_data.get("new_tier")
            }
        }
    
    elif last_worker == "payment_agent":
        payment_status = state.get("payment_status", {})
        if payment_status.get("success"):
            return {
                "message": "Payment successful!",
                "data": {"transaction_id": payment_status.get("transaction_id")}
            }
        else:
            return {
                "message": f"Payment failed: {payment_status.get('message')}",
                "prompt": "Please try again."
            }
    
    elif last_worker == "post_purchase_agent":
        return {
            "message": "Order confirmed! You'll receive tracking details soon.",
            "data": state.get("order_status", {})
        }
    
    else:
        return {
            "message": "How can I help you today?",
            "prompt": None
        }
