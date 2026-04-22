"""
sales_graph/state.py

SessionState schema for LangGraph orchestration.
Matches the design doc + your MongoDB schema.
"""

from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime


class SessionState(TypedDict, total=False):
    """
    Complete state object that flows through the LangGraph.
    Maps to both your MongoDB session schema and the design doc.
    """
    
    # ── Identity ────────────────────────────────────────────────────
    user_id: str                        # MongoDB ObjectId as string
    session_id: str                     # MongoDB session._id as string
    channel: str                        # "web" | "mobile" | "kiosk" | "whatsapp" | "telegram" | "voice"
    channel_history: List[str]          # All channels touched this session
    location: Optional[Dict[str, Any]]  # { lat, lng, store_id, city }
    
    # ── Latest User Input ───────────────────────────────────────────
    latest_user_message: str            # Current user message being processed
    
    # ── Customer Context ────────────────────────────────────────────
    customer_profile: Dict[str, Any]    # From MongoDB users collection
    # Structure: {name, email, preferences, loyalty: {tier, points}, payment_methods, past_purchases}
    
    conversation_summary: str           # LLM-generated running summary (optional)
    
    # ── Cart and Products ───────────────────────────────────────────
    cart_items: List[Dict[str, Any]]    # [{ product_id (ObjectId str), name, qty, price }]
    recommended_items: List[Dict[str, Any]]  # Output of recommendation_agent
    # Structure from RecommendationAgent: [{product_id, name, category, subcategory, price, ratings, image, score, signals, reason}]
    
    inventory_status: Dict[str, Any]    # Keyed by product_id (str)
    # Structure: {product_id: {success, totalStock, storeStock, isAvailable, productName}}
    
    inventory_verified: bool            # True if all cart items confirmed in stock
    inventory_checked_at: Optional[str] # ISO8601 timestamp for TTL validation
    
    # ── Offers and Pricing ──────────────────────────────────────────
    loyalty_data: Optional[Dict[str, Any]]  # Output of OfferLoyaltyAgent.process_checkout
    # Structure: {cart_total, coupon_discount, loyalty_points_used, loyalty_points_earned, final_amount, new_tier, order_id}
    
    # ── Fulfillment ─────────────────────────────────────────────────
    reservation_status: Optional[Dict[str, Any]]  # Pre-payment reservation info
    order_status: Optional[Dict[str, Any]]        # Post-payment order info from fulfillment
    # Structure from FulfillmentAgent: {success, order_id, status, fulfilled_items, unfulfilled_items, fulfillment_type}
    
    # ── Payment ─────────────────────────────────────────────────────
    payment_status: Optional[Dict[str, Any]]  # Output of PaymentAgent
    # Structure: {success, transaction_id, amount, payment_method, message}
    
    payment_idempotency_key: Optional[str]  # Generated once per cart state (see design doc §12)
    payment_method: Optional[str]           # Selected payment method for the current checkout
    payment_details: Optional[Dict[str, Any]]
    
    # ── Orchestration Control ───────────────────────────────────────
    current_intent: str                 # Latest classified intent (from intent_detector)
    intent_entities: Dict[str, Any]     # Extracted entities: {product_query, location, order_id, sku_list}
    
    next_action: str                    # Which worker to call next, or "respond"
    await_confirmation: bool            # If True, halt and surface response to user
    confirmation_context: Optional[str] # Template key for response_generator (e.g., "order_summary", "payment_retry")
    
    agent_call_history: List[str]       # Ordered list of agents called this session
    last_worker: Optional[str]          # Last worker agent that executed
    retry_count: Dict[str, int]         # Per-worker retry tracker {worker_name: count}
    
    silent_chains_this_turn: int        # Counter to enforce max 3 silent chains per turn
    
    # ── Stale Data Flags ────────────────────────────────────────────
    stale_flags: Dict[str, bool]        # {inventory: bool, loyalty: bool}
    
    # ── Response to User ────────────────────────────────────────────
    response: Optional[Dict[str, Any]]  # Final formatted response from response_generator
    # Structure: {message: str, data: {...}, prompt: str (optional)}
    
    # ── Error Tracking ──────────────────────────────────────────────
    last_error: Optional[Dict[str, Any]]  # Last error from a worker {code, message, worker}


# Helper function to initialize a new session state
def create_initial_state(user_id: str, session_id: str, channel: str, message: str) -> SessionState:
    """
    Creates initial state when a new session starts or user sends first message.
    """
    return SessionState(
        user_id=user_id,
        session_id=session_id,
        channel=channel,
        channel_history=[channel],
        location=None,
        latest_user_message=message,
        customer_profile={},  # Will be loaded by a node
        conversation_summary="",
        cart_items=[],
        recommended_items=[],
        inventory_status={},
        inventory_verified=False,
        inventory_checked_at=None,
        loyalty_data=None,
        reservation_status=None,
        order_status=None,
        payment_status=None,
        payment_idempotency_key=None,
        payment_method=None,
        payment_details=None,
        current_intent="",
        intent_entities={},
        next_action="",
        await_confirmation=False,
        confirmation_context=None,
        agent_call_history=[],
        last_worker=None,
        retry_count={},
        silent_chains_this_turn=0,
        stale_flags={"inventory": False, "loyalty": False},
        response=None,
        last_error=None
    )
