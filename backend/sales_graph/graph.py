"""
sales_graph/graph.py

Main LangGraph orchestration.
Implements the graph topology from design doc Section 6.
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from typing import Dict, Any

# Import state schema
from sales_graph.state import SessionState

# Import all node functions
from sales_graph.nodes.intent_detector import intent_detector_node
from sales_graph.nodes.sales_planner import sales_planner_node, post_worker_evaluation
from sales_graph.nodes.recommend import recommendation_agent_node
from sales_graph.nodes.inventory import inventory_agent_node
from sales_graph.nodes.response_generator import response_generator_node

# You'll need to create these following the same pattern as recommend.py and inventory.py
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


# ─── Helper function to invoke the graph ───────────────────────────
def run_sales_graph(user_id: str, session_id: str, channel: str, message: str) -> Dict[str, Any]:
    """
    Convenience function to run the graph with a user message.
    
    Args:
        user_id: MongoDB ObjectId as string
        session_id: MongoDB session._id as string  
        channel: "web" | "mobile" | "kiosk" etc
        message: User's text input
    
    Returns:
        Final state with response
    """
    
    # Create initial state
    from sales_graph.state import create_initial_state
    initial_state = create_initial_state(user_id, session_id, channel, message)
    
    # Define checkpoint config
    config = {
        "configurable": {
            "thread_id": f"{user_id}::{session_id}"  # Composite key per design doc
        }
    }
    
    # Run the graph
    final_state = sales_graph.invoke(initial_state, config=config)
    
    return final_state


# ─── Example Usage ──────────────────────────────────────────────────
if __name__ == "__main__":
    # Test the graph
    result = run_sales_graph(
        user_id="507f1f77bcf86cd799439011",  # Example ObjectId
        session_id="507f1f77bcf86cd799439012",
        channel="web",
        message="Show me blue kurtis"
    )
    
    print("Response:", result.get("response"))
