from db.database import sessions_collection
from datetime import datetime
import uuid

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
            "pending_action": None
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

def add_message(session_id, role, message):
    sessions_collection.update_one(
        {"_id": session_id},
        {
            "$push": {
                "chat_history": {
                    "role": role,
                    "message": message,
                    "timestamp": datetime.utcnow()
                }
            },
            "$currentDate": {"metadata.last_updated": True}
        }
    )

def update_session(session_id, updates):
    result = sessions_collection.update_one(
        {"_id": session_id},
        {
            "$set": updates,
            "$currentDate": {"metadata.last_updated": True}
        }
    )
    return get_session(session_id)

def end_session(session_id):
    """
    Mark session as completed.
    """
    result = sessions_collection.update_one(
        {"_id": session_id},
        {"$set": {"active": False, "updated_at": datetime.utcnow()}}
    )
    return result.modified_count > 0
