"""
sales_graph/nodes/sales_planner.py

The central orchestrator node.
Implements the planner policy from design doc Section 8.2.
"""

from typing import Dict, Any
from datetime import datetime, timedelta


# Max retries per worker (from design doc Section 11.2)
MAX_RETRIES = {
    "recommendation_agent": 1,
    "inventory_agent": 2,
    "cart_manager": 1,
    "loyalty_offers_agent": 1,
    "payment_agent": 2,
    "fulfilment_agent": 2,
    "post_purchase_agent": 1
}


def sales_planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    The planner reads intent + state and decides next_action.
    
    Returns updates to:
    - next_action: which worker to call, or "respond"
    - await_confirmation: if True, halt and surface response
    - confirmation_context: template key for response_generator
    - silent_chains_this_turn: incremented if silent chain
    """
    
    intent = state.get("current_intent", "")
    
    # Safety limit: max 3 silent chains per turn (design doc Section 16)
    if state.get("silent_chains_this_turn", 0) >= 3:
        return {
            "next_action": "respond",
            "await_confirmation": False,
            "confirmation_context": "max_chains_reached"
        }
    
    # Check if last worker had an error and needs retry
    if state.get("last_error"):
        retry_decision = handle_retry_logic(state)
        if retry_decision:
            return retry_decision
    
    # Main routing policy (from design doc Section 8.2)
    routing = planner_policy(intent, state)
    
    return routing


def planner_policy(intent: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Implements the routing policy from design doc Section 8.2.
    Pure rules-based for MVP. Can be upgraded to LLM later.
    """
    checkout_context = state.get("loyalty_data") or state.get("checkout_context") or {}
    checkout_context_matches = checkout_context_matches_cart(state)
    checkout_stage = state.get("checkout_stage")
    checkout_stage_active = checkout_stage in {"summary_ready", "awaiting_payment_method", "payment_in_progress"}
    
    # ── Discovery ───────────────────────────────────────────────────
    if intent == "discovery" or intent == "refine_recommendations":
        # After the recommendation worker runs in the current turn, respond.
        # On a fresh user turn, last_worker is reset in graph.py so we recompute.
        if state.get("last_worker") == "recommendation_agent":
            return {
                "next_action": "respond",
                "await_confirmation": False,
                "confirmation_context": None
            }
        return {
            "next_action": "recommendation_agent",
            "await_confirmation": False,
            "confirmation_context": None,
            "silent_chains_this_turn": state.get("silent_chains_this_turn", 0)
        }
    
    # ── Availability Check ──────────────────────────────────────────
    if intent == "availability_check":
        if state.get("last_worker") == "inventory_agent":
            return {
                "next_action": "respond",
                "await_confirmation": False,
                "confirmation_context": None
            }

        if not state.get("cart_items") and not state.get("recommended_items"):
            # No items to check
            return {
                "next_action": "respond",
                "await_confirmation": False,
                "confirmation_context": "no_items_to_check"
            }
        return {
            "next_action": "inventory_agent",
            "await_confirmation": False,
            "confirmation_context": None,
            "silent_chains_this_turn": state.get("silent_chains_this_turn", 0)
        }

    if intent in {"add_to_cart", "remove_from_cart", "view_cart"}:
        if state.get("last_worker") == "cart_manager":
            return {
                "next_action": "respond",
                "await_confirmation": False,
                "confirmation_context": None
            }
        return {
            "next_action": "cart_manager",
            "await_confirmation": False,
            "confirmation_context": None,
            "silent_chains_this_turn": state.get("silent_chains_this_turn", 0)
        }
    
    # ── Reservation Request ─────────────────────────────────────────
    if intent == "reservation_request":
        if not state.get("inventory_verified"):
            # Silently verify inventory first
            return {
                "next_action": "inventory_agent",
                "await_confirmation": False,
                "confirmation_context": None,
                "silent_chains_this_turn": state.get("silent_chains_this_turn", 0) + 1
            }
        # Inventory verified — gate on user confirmation
        return {
            "next_action": "respond",
            "await_confirmation": True,
            "confirmation_context": "reservation_summary"
        }
    
    # ── Offer Inquiry ───────────────────────────────────────────────
    if intent == "offer_inquiry":
        return {
            "next_action": "loyalty_offers_agent",
            "await_confirmation": False,
            "confirmation_context": None,
            "silent_chains_this_turn": state.get("silent_chains_this_turn", 0)
        }
    
    # ── Checkout Intent ─────────────────────────────────────────────
    if intent == "checkout_intent":
        if not state.get("cart_items"):
            return {
                "next_action": "respond",
                "await_confirmation": False,
                "confirmation_context": "empty_cart"
            }
        
        # Check if inventory is stale or not verified
        if not state.get("inventory_verified") or is_stale(state, "inventory"):
            return {
                "next_action": "inventory_agent",
                "await_confirmation": False,
                "confirmation_context": None,
                "silent_chains_this_turn": state.get("silent_chains_this_turn", 0) + 1
            }
        
        # Check if loyalty data is stale or missing
        if not checkout_context or is_stale(state, "loyalty") or not checkout_context_matches:
            return {
                "next_action": "loyalty_offers_agent",
                "await_confirmation": False,
                "confirmation_context": None,
                "silent_chains_this_turn": state.get("silent_chains_this_turn", 0) + 1
            }
        
        # All preconditions met — show order summary and gate
        return {
            "next_action": "respond",
            "await_confirmation": True,
            "confirmation_context": "order_summary",
            "checkout_stage": "summary_ready"
        }
    
    # ── Checkout Confirmation ───────────────────────────────────────
    if intent == "checkout_confirmation":
        chosen_payment_method = state.get("intent_entities", {}).get("payment_method") or state.get("payment_method")

        if state.get("last_worker") == "payment_agent":
            payment = state.get("payment_status") or {}
            if payment.get("success"):
                return {
                    "next_action": "fulfilment_agent",
                    "await_confirmation": False,
                    "confirmation_context": None,
                    "checkout_stage": "payment_in_progress",
                    "silent_chains_this_turn": state.get("silent_chains_this_turn", 0) + 1
                }
            return {
                "next_action": "respond",
                "await_confirmation": False,
                "confirmation_context": "payment_retry",
                "checkout_stage": "awaiting_payment_method"
            }

        if state.get("last_worker") == "fulfilment_agent":
            return {
                "next_action": "post_purchase_agent",
                "await_confirmation": False,
                "confirmation_context": None,
                "checkout_stage": "payment_in_progress",
                "silent_chains_this_turn": state.get("silent_chains_this_turn", 0) + 1
            }

        if state.get("last_worker") == "post_purchase_agent":
            return {
                "next_action": "respond",
                "await_confirmation": False,
                "confirmation_context": None,
                "checkout_stage": "completed"
            }

        if not chosen_payment_method:
            return {
                "next_action": "respond",
                "await_confirmation": True,
                "confirmation_context": "choose_payment_method",
                "checkout_stage": "awaiting_payment_method"
            }

        return {
            "next_action": "payment_agent",
            "await_confirmation": False,
            "confirmation_context": None,
            "payment_method": chosen_payment_method,
            "checkout_stage": "payment_in_progress",
            "silent_chains_this_turn": state.get("silent_chains_this_turn", 0)
        }

    if intent == "payment_method_selection":
        chosen_payment_method = state.get("intent_entities", {}).get("payment_method") or state.get("payment_method")
        in_checkout_flow = checkout_stage_active and (bool(checkout_context) or bool(state.get("cart_items")))
        if not in_checkout_flow:
            if state.get("cart_items") and chosen_payment_method:
                return {
                    "next_action": "loyalty_offers_agent",
                    "await_confirmation": False,
                    "confirmation_context": None,
                    "payment_method": chosen_payment_method,
                    "checkout_stage": "summary_ready",
                    "silent_chains_this_turn": state.get("silent_chains_this_turn", 0) + 1
                }
            return {
                "next_action": "respond",
                "await_confirmation": False,
                "confirmation_context": "checkout_context_lost"
            }

        if state.get("last_worker") == "payment_agent":
            payment = state.get("payment_status") or {}
            if payment.get("success"):
                return {
                    "next_action": "fulfilment_agent",
                    "await_confirmation": False,
                    "confirmation_context": None,
                    "checkout_stage": "payment_in_progress",
                    "silent_chains_this_turn": state.get("silent_chains_this_turn", 0) + 1
                }
            return {
                "next_action": "respond",
                "await_confirmation": False,
                "confirmation_context": "payment_retry",
                "checkout_stage": "awaiting_payment_method"
            }

        if state.get("last_worker") == "fulfilment_agent":
            return {
                "next_action": "post_purchase_agent",
                "await_confirmation": False,
                "confirmation_context": None,
                "checkout_stage": "payment_in_progress",
                "silent_chains_this_turn": state.get("silent_chains_this_turn", 0) + 1
            }

        if state.get("last_worker") == "post_purchase_agent":
            return {
                "next_action": "respond",
                "await_confirmation": False,
                "confirmation_context": None,
                "checkout_stage": "completed"
            }

        if not chosen_payment_method:
            return {
                "next_action": "respond",
                "await_confirmation": True,
                "confirmation_context": "choose_payment_method",
                "checkout_stage": "awaiting_payment_method"
            }

        if not checkout_context or not checkout_context_matches:
            if state.get("cart_items"):
                return {
                    "next_action": "loyalty_offers_agent",
                    "await_confirmation": False,
                    "confirmation_context": None,
                    "payment_method": chosen_payment_method,
                    "checkout_stage": "summary_ready",
                    "silent_chains_this_turn": state.get("silent_chains_this_turn", 0) + 1
                }
            return {
                "next_action": "respond",
                "await_confirmation": False,
                "confirmation_context": "checkout_context_lost"
            }

        return {
            "next_action": "payment_agent",
            "await_confirmation": False,
            "confirmation_context": None,
            "payment_method": chosen_payment_method,
            "checkout_stage": "payment_in_progress",
            "silent_chains_this_turn": state.get("silent_chains_this_turn", 0)
        }
    
    # ── Post-Purchase ───────────────────────────────────────────────
    if intent == "order_tracking" or intent == "return_request":
        if state.get("last_worker") == "post_purchase_agent":
            return {
                "next_action": "respond",
                "await_confirmation": False,
                "confirmation_context": None
            }
        return {
            "next_action": "post_purchase_agent",
            "await_confirmation": False,
            "confirmation_context": None,
            "silent_chains_this_turn": state.get("silent_chains_this_turn", 0)
        }
    
    # ── Fallback ────────────────────────────────────────────────────
    return {
        "next_action": "respond",
        "await_confirmation": False,
        "confirmation_context": "general_query"
    }


def handle_retry_logic(state: Dict[str, Any]) -> Dict[str, Any] | None:
    """
    Checks if the last error is retryable and hasn't exceeded max retries.
    Returns routing decision or None.
    """
    error = state.get("last_error") or {}
    worker = error.get("worker")
    retry_count = state.get("retry_count", {})
    
    if not worker:
        return None
    
    current_retries = retry_count.get(worker, 0)
    max_retries = MAX_RETRIES.get(worker, 0)
    
    if current_retries < max_retries and error.get("retryable", False):
        # Retry the same worker
        return {
            "next_action": worker,
            "await_confirmation": False,
            "confirmation_context": None,
            "retry_count": {**retry_count, worker: current_retries + 1}
        }
    else:
        # Max retries exceeded or non-retryable error
        return {
            "next_action": "respond",
            "await_confirmation": False,
            "confirmation_context": "error_response"
        }


def is_stale(state: Dict[str, Any], data_type: str) -> bool:
    """
    Checks if data is stale based on TTL (design doc Section 13).
    
    TTLs:
    - inventory: 15 minutes
    - loyalty: 30 minutes
    """
    TTL = {
        "inventory": timedelta(minutes=15),
        "loyalty": timedelta(minutes=30)
    }
    
    if data_type == "inventory":
        checked_at = state.get("inventory_checked_at")
    elif data_type == "loyalty":
        loyalty_data = state.get("loyalty_data") or state.get("checkout_context") or {}
        checked_at = loyalty_data.get("calculated_at")
    else:
        return True
    
    if not checked_at:
        return True
    
    try:
        checked_time = datetime.fromisoformat(checked_at)
        return datetime.utcnow() - checked_time > TTL[data_type]
    except:
        return True


def checkout_context_matches_cart(state: Dict[str, Any]) -> bool:
    checkout_context = state.get("loyalty_data") or state.get("checkout_context") or {}
    if not checkout_context:
        return False

    stored_signature = checkout_context.get("cart_signature")
    if not stored_signature:
        return False

    current_signature = _cart_signature(state.get("cart_items", []))
    return stored_signature == current_signature


def _cart_signature(cart_items: list[dict[str, Any]]) -> str:
    normalized_items = sorted(
        [
            (
                str(item.get("product_id")),
                int(item.get("qty", item.get("quantity", 1)) or 1),
                float(item.get("price", 0) or 0),
            )
            for item in (cart_items or [])
        ]
    )
    return "|".join(f"{product_id}:{qty}:{price}" for product_id, qty, price in normalized_items)


# ─── POST-WORKER SILENT CHAINING RULES (Design Doc Section 8.3) ───

def post_worker_evaluation(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    After a worker completes, decide if we should chain to another worker silently.
    Called by the graph after each worker node.
    
    Returns updated routing decision.
    """
    last_worker = state.get("last_worker")
    intent = state.get("current_intent")
    loyalty_data = state.get("loyalty_data") or state.get("checkout_context") or {}
    
    # Rule: recommendation_agent → inventory_agent (if cart has new items)
    if last_worker == "recommendation_agent" and intent == "discovery":
        if state.get("cart_items"):
            return {
                "next_action": "inventory_agent",
                "await_confirmation": False,
                "silent_chains_this_turn": state.get("silent_chains_this_turn", 0) + 1
            }
    
    # Rule: inventory_agent → loyalty_offers_agent (if checkout flow)
    if last_worker == "inventory_agent" and intent == "checkout_intent":
        if state.get("inventory_verified") and not loyalty_data:
            return {
                "next_action": "loyalty_offers_agent",
                "await_confirmation": False,
                "silent_chains_this_turn": state.get("silent_chains_this_turn", 0) + 1
            }
    
    # Rule: payment_agent → fulfilment_agent (if payment captured)
    if last_worker == "payment_agent":
        payment = state.get("payment_status") or {}
        if payment.get("success"):
            return {
                "next_action": "fulfilment_agent",
                "await_confirmation": False,
                "silent_chains_this_turn": state.get("silent_chains_this_turn", 0) + 1
            }
    
    # Rule: inventory_agent → recommendation_agent (if item unavailable)
    if last_worker == "inventory_agent":
        if state.get("last_error", {}).get("code") == "ITEM_UNAVAILABLE":
            return {
                "next_action": "recommendation_agent",
                "await_confirmation": False,
                "silent_chains_this_turn": state.get("silent_chains_this_turn", 0) + 1
            }
    
    # Default: respond to user (no more silent chaining)
    return {
        "next_action": "respond",
        "await_confirmation": False
    }
