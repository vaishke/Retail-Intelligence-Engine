"""
sales_graph/nodes/inventory.py

Wrapper node around agents/inventory_agent.py
"""

from typing import Dict, Any
from agents.inventory_agent import InventoryAgent
from datetime import datetime
from services.cart_service import CartService
from db.database import sessions_collection


def inventory_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Checks stock for cart items or recommended items.
    
    READS from state:
    - cart_items
    - recommended_items (fallback if no cart)
    - location (for store_id)
    
    WRITES to state:
    - inventory_status
    - inventory_verified
    - inventory_checked_at
    - last_worker
    - agent_call_history
    - last_error (if failure)
    """
    
    cart_items = state.get("cart_items", [])
    recommended_items = state.get("recommended_items", [])
    location = state.get("location", {})
    store_id = location.get("store_id") if location else None
    
    intent_entities = state.get("intent_entities", {})
    resolved_product = None

    if intent_entities.get("product_query") or intent_entities.get("reference"):
        resolved_product = CartService.resolve_product_reference(
            product_query=intent_entities.get("product_query") or intent_entities.get("reference", ""),
            recommended_items=recommended_items or _latest_recommendations_from_session(state.get("session_id")),
            cart_items=cart_items,
        )

    # Determine which items to check
    if resolved_product:
        items_to_check = [resolved_product]
    else:
        items_to_check = cart_items if cart_items else recommended_items
    
    if not items_to_check:
        return {
            "inventory_status": {},
            "inventory_verified": False,
            "last_error": {
                "code": "NO_ITEMS_TO_CHECK",
                "message": "No items in cart or recommendations",
                "worker": "inventory_agent",
                "retryable": False
            }
        }
    
    inventory_results = {}
    all_available = True
    unavailable_items = []
    
    try:
        for item in items_to_check:
            product_id = item.get("product_id")
            if not product_id:
                continue
            requested_quantity = int(item.get("qty", item.get("quantity", 1)) or 1)
            
            # Call your existing inventory agent
            result = InventoryAgent.check_stock(
                product_id=str(product_id),  # Convert ObjectId to string
                store_id=store_id,
                quantity=requested_quantity,
            )
            
            inventory_results[str(product_id)] = result
            
            if not result.get("isAvailable"):
                all_available = False
                unavailable_items.append(
                    {
                        "product_id": str(product_id),
                        "requested_quantity": requested_quantity,
                        "available_quantity": result.get("availableQuantity", 0),
                        "product_name": result.get("productName"),
                    }
                )
        
        # Success path
        updates = {
            "inventory_status": inventory_results,
            "inventory_verified": all_available,
            "inventory_checked_at": datetime.utcnow().isoformat(),
            "last_worker": "inventory_agent",
            "agent_call_history": state.get("agent_call_history", []) + ["inventory_agent"],
            "last_error": None
        }
        
        # If some items unavailable, set error for planner to handle
        if not all_available:
            updates["last_error"] = {
                "code": "ITEM_UNAVAILABLE",
                "message": f"{len(unavailable_items)} item(s) out of stock",
                "worker": "inventory_agent",
                "retryable": False,
                "unavailable_items": unavailable_items
            }
        
        return updates
    
    except Exception as e:
        return {
            "inventory_status": {},
            "inventory_verified": False,
            "last_worker": "inventory_agent",
            "agent_call_history": state.get("agent_call_history", []) + ["inventory_agent"],
            "last_error": {
                "code": "EXCEPTION",
                "message": str(e),
                "worker": "inventory_agent",
                "retryable": True  # API errors are retryable
            }
        }


def _latest_recommendations_from_session(session_id: str | None) -> list[Dict[str, Any]]:
    if not session_id:
        return []

    session = sessions_collection.find_one({"_id": session_id}, {"chat_history": 1})
    if not session:
        return []

    for entry in reversed(session.get("chat_history", [])):
        payload = entry.get("payload", {})
        recommendations = payload.get("data", {}).get("recommendations")
        if recommendations:
            return recommendations

    return []
