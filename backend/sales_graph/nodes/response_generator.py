"""
sales_graph/nodes/response_generator.py

Formats state into user-facing responses.
Uses templates, not LLM (for speed and cost efficiency).
"""

from typing import Dict, Any

from sales_graph.conversation_ai import get_recent_chat_turns, style_sales_response


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
    elif context == "checkout_context_lost":
        response = format_checkout_recovery(state)
    elif context == "max_chains_reached":
        response = {"message": "Processing... Please wait while I gather information for you.", "data": {}}
    else:
        # Default response based on last worker
        response = format_default_response(state)

    response = style_sales_response(
        response=response,
        state=state,
        recent_turns=get_recent_chat_turns(state.get("session_id")),
    )
    
    return {"response": response}


def format_order_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formats checkout confirmation with order summary.
    """
    loyalty_data = state.get("loyalty_data") or state.get("checkout_context") or {}
    cart_items = state.get("cart_items", [])
    
    return {
        "message": "Here’s a quick look at your order:",
        "data": {
            "items": cart_items,
            "cart_total": loyalty_data.get("cart_total", 0),
            "discount": loyalty_data.get("coupon_discount", 0),
            "points_used": loyalty_data.get("loyalty_points_used", 0),
            "final_amount": loyalty_data.get("final_amount", 0),
            "points_earned": loyalty_data.get("loyalty_points_earned", 0),
            "new_tier": loyalty_data.get("new_tier")
        },
        "prompt": "Whenever you're ready, I can help you continue to payment."
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
    loyalty_data = state.get("loyalty_data") or state.get("checkout_context") or {}
    final_amount = loyalty_data.get("final_amount", 0)

    return {
        "message": "You’re almost done. Please choose a payment method to complete your order.",
        "data": {
            "available_payment_methods": ["UPI", "CARD", "COD"],
            "final_amount": final_amount,
        },
        "prompt": "You can simply reply with UPI, Card, or Cash on Delivery."
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


def format_checkout_recovery(state: Dict[str, Any]) -> Dict[str, Any]:
    cart_items = state.get("cart_items", [])

    if cart_items:
        return {
            "message": "I was in the middle of checkout, so I just need to refresh the order details before we take payment.",
            "prompt": "Please say 'proceed to checkout' once more and I’ll pick it up from your cart.",
            "data": {"cart_items": cart_items}
        }

    return {
        "message": "I lost the active checkout context for that payment reply.",
        "prompt": "Please add items to your cart or start checkout again.",
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
            "message": f"I found {len(recommended_items)} option(s) you might like:",
            "data": {"recommendations": recommended_items},
            "prompt": "If one catches your eye, I can add it to your cart or check availability."
        }

    elif last_worker == "cart_manager":
        cart_items = state.get("cart_items", [])
        intent = state.get("current_intent")
        product_query = state.get("intent_entities", {}).get("product_query")

        if intent == "view_cart":
            if not cart_items:
                return {
                    "message": "Your cart is empty right now.",
                    "data": {"cart_items": []},
                    "prompt": "I can show you a few good picks if you’d like."
                }
            return {
                "message": f"You currently have {len(cart_items)} item(s) in your cart.",
                "data": {"cart_items": cart_items},
                "prompt": "Would you like me to check availability or help you move to checkout?"
            }

        if intent == "remove_from_cart":
            return {
                "message": f"I’ve removed {product_query or 'that item'} from your cart.",
                "data": {"cart_items": cart_items},
                "prompt": "Want to update anything else in the cart?"
            }

        added_item = cart_items[-1] if cart_items else None
        return {
            "message": f"Done — I’ve added {added_item.get('name', 'that item')} to your cart." if added_item else "Done — I’ve added that item to your cart.",
            "data": {"cart_items": cart_items},
            "prompt": "Would you like me to check availability, continue shopping, or help you place the order?"
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
                        "prompt": f"I found stock at {best_store} ({best_qty} units). Want me to add it to your cart or help you check out?"
                    }
                return {
                    "message": f"{product_name} is available.",
                    "data": {"inventory": item},
                    "prompt": f"There are {item.get('totalStock', 0)} units available. Would you like to go ahead with it?"
                }

            return {
                "message": f"{product_name} is currently out of stock.",
                "data": {"inventory": item},
                "prompt": "I can show you a few similar alternatives if you want."
            }

        if inventory_verified:
            return {
                "message": "Good news — everything in your cart is in stock.",
                "data": {"inventory": inventory_status},
                "prompt": "Would you like to move ahead to checkout?"
            }

            return {
                "message": "A few items are out of stock, but I can help with alternatives.",
                "prompt": None,
                "data": {"inventory": inventory_status}
            }
    
    elif last_worker == "loyalty_offers_agent":
        loyalty_data = state.get("loyalty_data") or state.get("checkout_context") or {}
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
        if state.get("current_intent") == "order_tracking" or order_status.get("tracking_lookup"):
            if order_status.get("listing_orders"):
                recent_orders = order_status.get("recent_orders", [])
                return {
                    "message": "Here are your most recent orders:",
                    "data": {"recent_orders": recent_orders},
                    "prompt": "If you want details for one of them, just say 'track order' followed by the order id."
                }

            tracking_status = order_status.get("tracking_status", "processing")
            order_id = order_status.get("order_id")
            return {
                "message": f"Here’s the latest update for order {order_id}.",
                "data": {
                    "order_id": order_id,
                    "order_status": order_status.get("status"),
                    "tracking_status": tracking_status,
                    "tracking_number": order_status.get("tracking_number"),
                    "shipment_id": order_status.get("shipment_id"),
                    "invoice_id": order_status.get("invoice_id"),
                    "created_at": order_status.get("created_at"),
                    "confirmed_at": order_status.get("confirmed_at"),
                    "final_amount": order_status.get("final_amount"),
                    "items": order_status.get("items", []),
                },
                "prompt": "If you'd like, I can also show your recent orders."
            }

        checkout_points = order_status.get("points_earned_at_checkout", 0)
        bonus_points = order_status.get("bonus_points", 0)
        loyalty_total = order_status.get("loyalty_points_total")
        loyalty_tier = order_status.get("loyalty_tier")

        message = "Your order is confirmed and the payment went through successfully."
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
            "message": "What would you like to shop for today?",
            "prompt": None,
            "data": {}
        }
