from db.database import sessions_collection
from datetime import datetime
import uuid

from services.recommendation_state_service import initialize_recommendation_state

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
            "recommendation_state": {}
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
