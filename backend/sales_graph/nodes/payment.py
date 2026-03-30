"""
sales_graph/nodes/payment.py

Wrapper node around agents/payment_agent.py
Implements payment idempotency (Design Doc Section 12)
"""

from typing import Dict, Any
from agents.payment_agent import PaymentAgent
from bson import ObjectId
import hashlib
import json


def payment_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls PaymentAgent with idempotency protection.
    
    READS from state:
    - loyalty_data (to get order_id and final_amount)
    - payment_method (from user selection)
    - payment_details (optional)
    - cart_items (for idempotency key generation)
    - session_id
    - payment_idempotency_key (if already generated)
    
    WRITES to state:
    - payment_status
    - payment_idempotency_key
    - last_worker
    - agent_call_history
    - last_error (if failure)
    """
    
    loyalty_data = state.get("loyalty_data", {})
    order_id = loyalty_data.get("order_id")
    
    if not order_id:
        return {
            "payment_status": None,
            "last_worker": "payment_agent",
            "agent_call_history": state.get("agent_call_history", []) + ["payment_agent"],
            "last_error": {
                "code": "NO_ORDER_ID",
                "message": "Order must be created before payment",
                "worker": "payment_agent",
                "retryable": False
            }
        }
    
    # Generate idempotency key (Design Doc Section 12)
    idempotency_key = state.get("payment_idempotency_key")
    if not idempotency_key:
        cart_hash = hashlib.sha256(
            json.dumps(state.get("cart_items", []), sort_keys=True).encode()
        ).hexdigest()[:16]
        idempotency_key = f"{state['session_id']}_{cart_hash}"
    
    # Get payment method from state (set by user or default to UPI)
    payment_method = state.get("payment_method", "UPI")
    payment_details = state.get("payment_details")
    
    try:
        # Call your existing payment agent
        # order_id is stored as string in state (converted in loyalty_offers node)
        # so we convert back to ObjectId for MongoDB lookup
        result = PaymentAgent.process_payment(
            order_id=ObjectId(order_id),
            payment_method=payment_method,
            details=payment_details
        )
        if result.get("success"):
            # Payment successful
            return {
                "payment_status": result,
                "payment_idempotency_key": idempotency_key,
                "last_worker": "payment_agent",
                "agent_call_history": state.get("agent_call_history", []) + ["payment_agent"],
                "last_error": None
            }
        else:
            # Payment failed (gateway declined, insufficient funds, etc.)
            return {
                "payment_status": result,
                "payment_idempotency_key": idempotency_key,
                "last_worker": "payment_agent",
                "agent_call_history": state.get("agent_call_history", []) + ["payment_agent"],
                "last_error": {
                    "code": "PAYMENT_FAILED",
                    "message": result.get("message", "Payment failed"),
                    "worker": "payment_agent",
                    "retryable": True  # User can retry or change payment method
                }
            }
    
    except Exception as e:
        # Unexpected exception
        return {
            "payment_status": None,
            "payment_idempotency_key": idempotency_key,
            "last_worker": "payment_agent",
            "agent_call_history": state.get("agent_call_history", []) + ["payment_agent"],
            "last_error": {
                "code": "EXCEPTION",
                "message": str(e),
                "worker": "payment_agent",
                "retryable": True  # Gateway timeout or network issue
            }
        }
