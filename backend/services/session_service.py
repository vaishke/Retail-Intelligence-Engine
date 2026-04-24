from db.database import orders_collection, sessions_collection
from datetime import datetime
import uuid
from bson import ObjectId
from bson.errors import InvalidId

from services.recommendation_state_service import initialize_recommendation_state


DURABLE_GRAPH_CONTEXT_DEFAULTS = {
    "checkout_context": None,
    "checkout_stage": None,
    "payment_method": None,
    "payment_idempotency_key": None,
    "loyalty_data": None,
}

def create_session(user_id, channel):
    session_id = str(uuid.uuid4())

    session_doc = {
        "_id": session_id,
        "user_id": user_id,

        "title": "New Chat",
        "channel": channel,
        "status": "active",

        "chat_history": [],

        "context": {
            "current_intent": None,
            "selected_products": [],
            "last_recommendations": [],
            "last_viewed_product": None,
            "pending_action": None,
            "recommendation_state": {},
            **DURABLE_GRAPH_CONTEXT_DEFAULTS,
        },

        "metadata": {
            "created_at": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        }
    }

    sessions_collection.insert_one(session_doc)
    return session_doc

def get_session(session_id):
    """
    Fetch an existing session by session_id.
    """
    return sessions_collection.find_one({"_id": session_id})

def add_message(session_id, role, message, payload=None):
    session = get_session(session_id)
    if not session:
        return

    chat_entry = {
        "role": role,
        "message": message,
        "timestamp": datetime.utcnow()
    }
    if payload is not None:
        chat_entry["payload"] = payload

    update_doc = {
        "$push": {
            "chat_history": chat_entry
        },
        "$currentDate": {"metadata.last_updated": True}
    }

    # Use the first user message as a human-friendly chat title.
    if role == "user" and not session.get("chat_history"):
        title = message.strip()[:60] or "New Chat"
        update_doc["$set"] = {"title": title}

    sessions_collection.update_one({"_id": session_id}, update_doc)

def update_session(session_id, updates):
    result = sessions_collection.update_one(
        {"_id": session_id},
        {
            "$set": updates,
            "$currentDate": {"metadata.last_updated": True}
        }
    )
    return get_session(session_id)


def get_recommendation_state(session_id):
    session = get_session(session_id)
    if not session:
        return initialize_recommendation_state({})

    context = session.get("context", {})
    return initialize_recommendation_state(context.get("recommendation_state"))


def save_recommendation_state(session_id, recommendation_state):
    sessions_collection.update_one(
        {"_id": session_id},
        {
            "$set": {
                "context.recommendation_state": initialize_recommendation_state(recommendation_state)
            },
            "$currentDate": {"metadata.last_updated": True}
        }
    )
    return get_recommendation_state(session_id)


def get_durable_graph_context(session_id):
    session = get_session(session_id)
    if not session:
        return dict(DURABLE_GRAPH_CONTEXT_DEFAULTS)

    context = session.get("context", {})
    durable_context = dict(DURABLE_GRAPH_CONTEXT_DEFAULTS)
    for key in DURABLE_GRAPH_CONTEXT_DEFAULTS:
        durable_context[key] = context.get(key)
    return durable_context


def recover_checkout_context(user_id, session_id, cart_items=None):
    user_oid = _to_object_id(user_id)
    if user_oid is None:
        return dict(DURABLE_GRAPH_CONTEXT_DEFAULTS)

    current_signature = _cart_signature(cart_items or [])
    query = {
        "user_id": user_oid,
        "$or": [
            {"session_id": session_id},
            {"session_id": None},
        ],
        "payment.status": {"$nin": ["paid", "success", "captured"]},
    }

    pending_orders = list(
        orders_collection.find(query).sort("created_at", -1).limit(5)
    )

    matched_order = None
    for order in pending_orders:
        order_signature = _cart_signature(order.get("items", []))
        if current_signature and order_signature == current_signature:
            matched_order = order
            break

    if matched_order is None and pending_orders:
        matched_order = pending_orders[0]

    if matched_order is None:
        return dict(DURABLE_GRAPH_CONTEXT_DEFAULTS)

    checkout_context = {
        "order_id": str(matched_order.get("_id")),
        "final_amount": matched_order.get("final_price", 0),
        "cart_signature": _cart_signature(matched_order.get("items", [])),
        "calculated_at": _make_iso(matched_order.get("created_at")),
    }

    payment_method = (matched_order.get("payment") or {}).get("method")
    checkout_stage = "awaiting_payment_method"
    if payment_method:
        checkout_stage = "payment_in_progress"

    return {
        "checkout_context": checkout_context,
        "checkout_stage": checkout_stage,
        "payment_method": payment_method,
        "payment_idempotency_key": None,
        "loyalty_data": checkout_context,
    }


def save_durable_graph_context(session_id, state):
    durable_context = dict(DURABLE_GRAPH_CONTEXT_DEFAULTS)
    state = state or {}

    for key in DURABLE_GRAPH_CONTEXT_DEFAULTS:
        durable_context[key] = state.get(key)

    sessions_collection.update_one(
        {"_id": session_id},
        {
            "$set": {
                **{f"context.{key}": value for key, value in durable_context.items()}
            },
            "$currentDate": {"metadata.last_updated": True}
        }
    )

    return durable_context


def _to_object_id(value):
    if isinstance(value, ObjectId):
        return value
    try:
        return ObjectId(str(value))
    except (InvalidId, TypeError):
        return None


def _cart_signature(cart_items):
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


def _make_iso(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return None

def delete_session(session_id):
    result = sessions_collection.delete_one({"_id": session_id})
    return result.deleted_count > 0

def end_session(session_id):
    """
    Mark session as completed.
    """
    result = sessions_collection.update_one(
        {"_id": session_id},
        {
            "$set": {"status": "completed"},
            "$currentDate": {"metadata.last_updated": True}
        }
    )
    return result.modified_count > 0
