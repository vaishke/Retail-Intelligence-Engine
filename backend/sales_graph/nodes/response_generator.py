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
    elif context == "choose_payment_method":
        response = format_choose_payment_method(state)
    elif context == "reservation_summary":
        response = format_reservation_summary(state)
    elif context == "payment_retry":
        response = format_payment_retry(state)
    elif context == "empty_cart":
        response = {"message": "Your cart is empty. Would you like some recommendations?", "data": {}}
    elif context == "no_items_to_check":
        response = {"message": "Please add items to your cart or get recommendations first.", "data": {}}
    elif context == "error_response":
        response = format_error_response(state)
    elif context == "max_chains_reached":
        response = {"message": "Processing... Please wait while I gather information for you.", "data": {}}
    else:
        # Default response based on last worker
        response = format_default_response(state)
    
    return {"response": response}


def format_order_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formats checkout confirmation with order summary.
    """
    loyalty_data = state.get("loyalty_data") or {}
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
    inventory_status = state.get("inventory_status") or {}
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
    payment_status = state.get("payment_status") or {}
    payment_method = payment_status.get("payment_method") or state.get("payment_method") or "UPI"
    
    return {
        "message": f"Payment via {payment_method} failed: {payment_status.get('message', 'Unknown error')}",
        "prompt": "Would you like to retry or choose a different mock payment method?"
    }


def format_choose_payment_method(state: Dict[str, Any]) -> Dict[str, Any]:
    loyalty_data = state.get("loyalty_data") or {}
    final_amount = loyalty_data.get("final_amount", 0)

    return {
        "message": "Please choose a payment method to complete your order.",
        "data": {
            "available_payment_methods": ["UPI", "CARD", "COD"],
            "final_amount": final_amount,
        },
        "prompt": "You can reply with: UPI, Card, or Cash on Delivery."
    }


def format_error_response(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formats generic error response.
    """
    error = state.get("last_error") or {}

    if error.get("code") == "NO_MATCHING_PRODUCTS":
        product_query = state.get("intent_entities", {}).get("product_query")
        if product_query:
            return {
                "message": f"I couldn't find an exact match for '{product_query}'.",
                "prompt": "Try a broader search, a different category, or a price range and I'll look again.",
                "data": {}
            }
        return {
            "message": "I couldn't find matching products for that request.",
            "prompt": "Try a broader search, a different category, or a price range and I'll look again.",
            "data": {}
        }

    if error.get("code") == "PRODUCT_NOT_RESOLVED":
        return {
            "message": "I couldn't figure out which product you meant.",
            "prompt": "Try naming the product again or pick one from the latest recommendations.",
            "data": {}
        }
    
    return {
        "message": f"Sorry, something went wrong: {error.get('message', 'Unknown error')}",
        "prompt": "Please try again or let me know if you need help with something else.",
        "data": {}
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

    elif last_worker == "cart_manager":
        cart_items = state.get("cart_items", [])
        intent = state.get("current_intent")
        product_query = state.get("intent_entities", {}).get("product_query")

        if intent == "view_cart":
            if not cart_items:
                return {
                    "message": "Your cart is empty.",
                    "data": {"cart_items": []},
                    "prompt": "Would you like some recommendations?"
                }
            return {
                "message": f"You have {len(cart_items)} item(s) in your cart.",
                "data": {"cart_items": cart_items},
                "prompt": "Would you like me to check availability or proceed to checkout?"
            }

        if intent == "remove_from_cart":
            return {
                "message": f"Removed {product_query or 'that item'} from your cart.",
                "data": {"cart_items": cart_items},
                "prompt": "Anything else you want to update?"
            }

        added_item = cart_items[-1] if cart_items else None
        return {
            "message": f"Added {added_item.get('name', 'that item')} to your cart." if added_item else "Added the item to your cart.",
            "data": {"cart_items": cart_items},
            "prompt": "Would you like me to check availability or continue shopping?"
        }
    
    elif last_worker == "inventory_agent":
        inventory_status = state.get("inventory_status") or {}
        inventory_verified = state.get("inventory_verified", False)

        if len(inventory_status) == 1:
            item = next(iter(inventory_status.values()))
            product_name = item.get("productName", "This item")
            if item.get("isAvailable"):
                store_stock = item.get("storeStock")
                if isinstance(store_stock, dict) and store_stock:
                    best_store, best_qty = max(store_stock.items(), key=lambda entry: entry[1])
                    return {
                        "message": f"{product_name} is available.",
                        "data": {"inventory": item},
                        "prompt": f"I found stock at {best_store} ({best_qty} units). Would you like to add it to your cart or proceed to checkout?"
                    }
                return {
                    "message": f"{product_name} is available.",
                    "data": {"inventory": item},
                    "prompt": f"There are {item.get('totalStock', 0)} units available. Would you like to proceed?"
                }

            return {
                "message": f"{product_name} is currently out of stock.",
                "data": {"inventory": item},
                "prompt": "Would you like me to suggest alternatives?"
            }

        if inventory_verified:
            return {
                "message": "Great news! All items in your cart are in stock.",
                "data": {"inventory": inventory_status},
                "prompt": "Would you like to proceed to checkout?"
            }

        return {
            "message": "Some items are out of stock. Let me suggest alternatives.",
            "prompt": None,
            "data": {"inventory": inventory_status}
        }
    
    elif last_worker == "loyalty_offers_agent":
        loyalty_data = state.get("loyalty_data") or {}
        return {
            "message": f"Your current loyalty tier: {loyalty_data.get('new_tier', 'Silver')}",
            "data": {
                "points": loyalty_data.get("loyalty_points_earned", 0),
                "tier": loyalty_data.get("new_tier")
            }
        }
    
    elif last_worker == "payment_agent":
        payment_status = state.get("payment_status") or {}
        if payment_status.get("success"):
            return {
                "message": f"Payment successful via {payment_status.get('payment_method', 'UPI')}.",
                "data": {
                    "transaction_id": payment_status.get("transaction_id"),
                    "gateway": payment_status.get("gateway", "mock")
                }
            }
        else:
            return {
                "message": f"Payment failed: {payment_status.get('message')}",
                "prompt": "Please try again."
            }
    
    elif last_worker == "post_purchase_agent":
        order_status = state.get("order_status") or {}
        payment_status = state.get("payment_status") or {}
        checkout_points = order_status.get("points_earned_at_checkout", 0)
        bonus_points = order_status.get("bonus_points", 0)
        loyalty_total = order_status.get("loyalty_points_total")
        loyalty_tier = order_status.get("loyalty_tier")

        message = "Order placed successfully! Your payment was completed."
        if checkout_points or bonus_points:
            message += f" You earned {checkout_points} checkout points"
            if bonus_points:
                message += f" and {bonus_points} bonus points"
            message += "."
        if loyalty_total is not None:
            message += f" Your total loyalty points are now {loyalty_total}."

        return {
            "message": message,
            "data": {
                **order_status,
                "payment_method": payment_status.get("payment_method"),
                "transaction_id": payment_status.get("transaction_id"),
                "loyalty_points_total": loyalty_total,
                "loyalty_tier": loyalty_tier,
            }
        }

    elif last_worker == "fulfilment_agent":
        order_status = state.get("order_status") or {}
        status = order_status.get("status")
        if status == "FULFILLED":
            return {
                "message": "Your order has been fulfilled successfully.",
                "data": order_status,
                "prompt": "We'll continue with order confirmation and delivery updates."
            }
        if status == "PARTIALLY_FULFILLED":
            return {
                "message": "Some items in your order could not be fulfilled.",
                "data": order_status,
                "prompt": "Please review the fulfilled items before we continue."
            }
        return {
            "message": "We couldn't fulfill your order right now.",
            "data": order_status,
            "prompt": "Would you like me to suggest alternatives or try a different store?"
        }
    
    else:
        return {
            "message": "How can I help you today?",
            "prompt": None,
            "data": {}
        }
