"""
sales_graph/nodes/recommend.py

Wrapper node around agents/recommendation_agent.py
"""

from typing import Dict, Any
from agents.recommendation_agent import RecommendationAgent
from datetime import datetime


def recommendation_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls RecommendationAgent and updates state with results.
    
    READS from state:
    - user_id
    - intent_entities (for constraints)
    - cart_items (for exclusion)
    
    WRITES to state:
    - recommended_items
    - last_worker
    - agent_call_history
    - last_error (if failure)
    """
    
    user_id = state.get("user_id")
    intent_entities = state.get("intent_entities", {})
    cart_items = state.get("cart_items", [])
    
    # Build constraints from intent entities
    constraints = build_constraints(intent_entities)
    
    # Get product IDs to exclude (already in cart)
    exclude_ids = [item.get("product_id") for item in cart_items if item.get("product_id")]
    
    try:
        # Call your existing recommendation agent
        print("DEBUG constraints:", constraints)
        print("DEBUG intent_entities:", intent_entities)
        result = RecommendationAgent.recommend_products(
            user_id=user_id,
            constraints=constraints,
            top_k=5,
            exclude_product_ids=exclude_ids
        )
        
        if result.get("success"):
            # Success path
            return {
                "recommended_items": result.get("recommendations", []),
                "last_worker": "recommendation_agent",
                "agent_call_history": state.get("agent_call_history", []) + ["recommendation_agent"],
                "last_error": None  # Clear any previous error
            }
        else:
            # Agent returned error
            return {
                "recommended_items": [],
                "last_worker": "recommendation_agent",
                "agent_call_history": state.get("agent_call_history", []) + ["recommendation_agent"],
                "last_error": {
                    "code": result.get("reason", "UNKNOWN_ERROR"),
                    "message": f"Recommendation failed: {result.get('reason')}",
                    "worker": "recommendation_agent",
                    "retryable": result.get("reason") == "CATALOGUE_API_UNAVAILABLE"
                }
            }
    
    except Exception as e:
        # Unexpected exception
        return {
            "recommended_items": [],
            "last_worker": "recommendation_agent",
            "agent_call_history": state.get("agent_call_history", []) + ["recommendation_agent"],
            "last_error": {
                "code": "EXCEPTION",
                "message": str(e),
                "worker": "recommendation_agent",
                "retryable": False
            }
        }


def build_constraints(entities: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts intent entities into RecommendationAgent constraints.
    """
    constraints = {}
    
    if entities.get("category"):
        constraints["category"] = entities["category"]

    if entities.get("subcategory"):
        constraints["subcategory"] = entities["subcategory"]

    if entities.get("tags"):
        constraints["tags"] = entities["tags"]
    
    if entities.get("price_range"):
        constraints["price_range"] = entities["price_range"]
    
    if entities.get("color"):
        constraints["colors"] = [entities["color"]]
    
    return constraints