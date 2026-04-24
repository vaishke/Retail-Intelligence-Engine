"""
sales_graph/graph.py

Main LangGraph orchestration.
Implements the graph topology from design doc Section 6.
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from typing import Dict, Any

from sales_graph.state import SessionState
from services.cart_service import CartService
from services.session_service import get_durable_graph_context, recover_checkout_context

from sales_graph.nodes.intent_detector import intent_detector_node
from sales_graph.nodes.sales_planner import sales_planner_node, post_worker_evaluation
from sales_graph.nodes.recommend import recommendation_agent_node
from sales_graph.nodes.inventory import inventory_agent_node
from sales_graph.nodes.cart_manager import cart_manager_node
from sales_graph.nodes.response_generator import response_generator_node
from sales_graph.nodes.loyalty_offers import loyalty_offers_agent_node
from sales_graph.nodes.payment import payment_agent_node
from sales_graph.nodes.fulfilment import fulfilment_agent_node
from sales_graph.nodes.post_purchase import post_purchase_agent_node


def create_sales_graph():
    """
    Creates and compiles the LangGraph.
    """
    
    # Initialize the graph with SessionState schema
    graph = StateGraph(SessionState)
    
    # ─── Add Nodes ──────────────────────────────────────────────────
    graph.add_node("intent_detector", intent_detector_node)
    graph.add_node("sales_planner", sales_planner_node)
    graph.add_node("recommendation_agent", recommendation_agent_node)
    graph.add_node("inventory_agent", inventory_agent_node)
    graph.add_node("cart_manager", cart_manager_node)
    graph.add_node("response_generator", response_generator_node)
    
    graph.add_node("loyalty_offers_agent", loyalty_offers_agent_node)
    graph.add_node("payment_agent", payment_agent_node)
    graph.add_node("fulfilment_agent", fulfilment_agent_node)
    graph.add_node("post_purchase_agent", post_purchase_agent_node)
    
    # ─── Set Entry Point ────────────────────────────────────────────
    graph.set_entry_point("intent_detector")
    
    # ─── Add Fixed Edges ────────────────────────────────────────────
    # intent_detector always goes to sales_planner
    graph.add_edge("intent_detector", "sales_planner")
    
    # All workers always return to sales_planner
    graph.add_edge("recommendation_agent", "sales_planner")
    graph.add_edge("inventory_agent", "sales_planner")
    graph.add_edge("cart_manager", "sales_planner")
    graph.add_edge("loyalty_offers_agent", "sales_planner")
    graph.add_edge("payment_agent", "sales_planner")
    graph.add_edge("fulfilment_agent", "sales_planner")
    graph.add_edge("post_purchase_agent", "sales_planner")
    
    # response_generator always goes to END
    graph.add_edge("response_generator", END)
    
    # ─── Add Conditional Edges from sales_planner ──────────────────
    def route_from_planner(state: Dict[str, Any]) -> str:
        """
        Routing function for conditional edges from sales_planner.
        Reads state.next_action and routes accordingly.
        """
        next_action = state.get("next_action", "respond")
        await_confirmation = state.get("await_confirmation", False)
        
        # If await_confirmation is True, always go to response_generator
        if await_confirmation:
            return "response_generator"
        
        # Otherwise route based on next_action
        return next_action
    
    graph.add_conditional_edges(
        "sales_planner",
        route_from_planner,
        {
            "recommendation_agent": "recommendation_agent",
            "inventory_agent": "inventory_agent",
            "cart_manager": "cart_manager",
            "loyalty_offers_agent": "loyalty_offers_agent",
            "payment_agent": "payment_agent",
            "fulfilment_agent": "fulfilment_agent",
            "post_purchase_agent": "post_purchase_agent",
            "respond": "response_generator",
            "response_generator": "response_generator"  # Explicit mapping
        }
    )
    
    # ─── Compile with Checkpointer ──────────────────────────────────
    # For local dev: SQLite checkpointer
    # For production: replace with PostgresSaver
    checkpointer = InMemorySaver()
    
    compiled_graph = graph.compile(checkpointer=checkpointer)
    
    return compiled_graph


# ─── Export the compiled graph ──────────────────────────────────────
sales_graph = create_sales_graph()
_seen_threads: set = set()


def _load_shared_cart(user_id: str) -> list[Dict[str, Any]]:
    cart_result = CartService.get_cart(user_id)
    if not cart_result.get("success"):
        return []
    return cart_result.get("cart", [])


def _load_durable_state(session_id: str, user_id: str, cart_items: list[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    durable_context = get_durable_graph_context(session_id)
    state = {
        "checkout_context": durable_context.get("checkout_context"),
        "checkout_stage": durable_context.get("checkout_stage"),
        "payment_method": durable_context.get("payment_method"),
        "payment_idempotency_key": durable_context.get("payment_idempotency_key"),
        "loyalty_data": durable_context.get("loyalty_data"),
    }
    if state.get("checkout_context"):
        return state

    recovered_context = recover_checkout_context(
        user_id=user_id,
        session_id=session_id,
        cart_items=cart_items or [],
    )
    for key, value in recovered_context.items():
        if state.get(key) is None:
            state[key] = value
    return state


# ─── Helper function to invoke the graph ───────────────────────────
def run_sales_graph(
    user_id: str,
    session_id: str,
    channel: str,
    message: str,
    extras: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Convenience function to run the graph with a user message.
    On the FIRST turn for a thread, full initial state is passed.
    On SUBSEQUENT turns, only the new message (and extras) are passed
    so the checkpointer can restore conversation history / cart / recommendations.
    """

    thread_id = f"{user_id}::{session_id}"
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    is_first_turn = thread_id not in _seen_threads

    if is_first_turn:
        # First message in this session — build full initial state
        from sales_graph.state import create_initial_state
        input_state = create_initial_state(user_id, session_id, channel, message)
        input_state["cart_items"] = _load_shared_cart(user_id)
        input_state.update(_load_durable_state(session_id, user_id, input_state["cart_items"]))
        _seen_threads.add(thread_id)
    else:
        # Subsequent messages — only send the fields that change each turn.
        # The checkpointer restores cart, recommendations, conversation_history, etc.
        input_state = {
            "latest_user_message": message,
            "cart_items": _load_shared_cart(user_id),
            "current_intent": None,       # reset so intent_detector runs fresh
            "intent_entities": {},
            "conversation_act": None,
            "intent_confidence": None,
            "next_action": None,
            "await_confirmation": False,
            "confirmation_context": None,
            "last_worker": None,
            "last_error": None,
            "silent_chains_this_turn": 0,
            "response": None,
            "agent_call_history": [],
        }
        input_state.update(_load_durable_state(session_id, user_id, input_state["cart_items"]))

    # Patch in any extra fields from the API request
    if extras:
        for key, value in extras.items():
            if value is not None:
                input_state[key] = value

    final_state = sales_graph.invoke(input_state, config=config)
    return final_state
