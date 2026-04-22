"""
sales_graph/nodes/cart_manager.py

Handles add/view/remove cart actions and syncs graph state with MongoDB.
"""

from typing import Dict, Any

from services.cart_service import CartService
from db.database import sessions_collection


def cart_manager_node(state: Dict[str, Any]) -> Dict[str, Any]:
    intent = state.get("current_intent")
    user_id = state.get("user_id")
    session_id = state.get("session_id")
    entities = state.get("intent_entities", {})

    if intent == "view_cart":
        cart_result = CartService.get_cart(user_id)
        if not cart_result.get("success"):
            return _error(state, "CART_LOAD_FAILED", cart_result.get("message", "Unable to load cart"))

        return {
            "cart_items": cart_result.get("cart", []),
            "last_worker": "cart_manager",
            "agent_call_history": state.get("agent_call_history", []) + ["cart_manager"],
            "last_error": None,
        }

    resolved_product = CartService.resolve_product_reference(
        product_query=entities.get("product_query") or entities.get("reference", ""),
        recommended_items=state.get("recommended_items", []) or _latest_recommendations_from_session(session_id),
        cart_items=state.get("cart_items", []),
    )

    if not resolved_product:
        return _error(state, "PRODUCT_NOT_RESOLVED", "I couldn't figure out which product you meant.")

    product_id = resolved_product.get("product_id")
    quantity = entities.get("quantity", 1) or 1

    existing_qty = next(
        (
            item.get("qty", item.get("quantity", 1))
            for item in state.get("cart_items", [])
            if item.get("product_id") == product_id
        ),
        0,
    )

    target_quantity = 0 if intent == "remove_from_cart" else existing_qty + quantity

    result = CartService.add_or_update_item(
        user_id=user_id,
        product_id=product_id,
        quantity=target_quantity,
        session_id=session_id,
    )

    if not result.get("success"):
        return _error(state, "CART_UPDATE_FAILED", result.get("message", "Unable to update cart"))

    return {
        "cart_items": result.get("cart", []),
        "last_worker": "cart_manager",
        "agent_call_history": state.get("agent_call_history", []) + ["cart_manager"],
        "last_error": None,
    }


def _error(state: Dict[str, Any], code: str, message: str) -> Dict[str, Any]:
    return {
        "last_worker": "cart_manager",
        "agent_call_history": state.get("agent_call_history", []) + ["cart_manager"],
        "last_error": {
            "code": code,
            "message": message,
            "worker": "cart_manager",
            "retryable": False,
        },
    }


def _latest_recommendations_from_session(session_id: str) -> list[Dict[str, Any]]:
    if not session_id:
        return []

    session = sessions_collection.find_one({"_id": session_id}, {"chat_history": 1})
    if not session:
        return []

    chat_history = session.get("chat_history", [])
    for entry in reversed(chat_history):
        payload = entry.get("payload", {})
        recommendations = payload.get("data", {}).get("recommendations")
        if recommendations:
            return recommendations

    return []
