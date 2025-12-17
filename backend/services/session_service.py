from db.database import sessions_collection
from datetime import datetime
import uuid

def create_session(user_id, channel):
    """
    Create a new session for the user.
    """
    session_id = str(uuid.uuid4())
    session_doc = {
        "_id": session_id,
        "user_id": user_id,
        "active_channel": channel,
        "context": {
            "intent": None,
            "current_category": None,
            "selected_products": [],
            "cart_order_id": None,
            "last_agent": None,
            "last_step": None,
            "recommendations": [],
            "stock_status": [],
            "offers_applied": [],
            "payment_status": None,
            "transaction_id": None,
            "fulfillment_status": None,
            "final_amount": 0
        },
        "channel_history": [{"channel": channel, "at": datetime.utcnow()}],
        "updated_at": datetime.utcnow(),
        "active": True
    }
    sessions_collection.insert_one(session_doc)
    return session_doc

def get_session(session_id):
    """
    Fetch an existing session by session_id.
    """
    return sessions_collection.find_one({"_id": session_id})

def update_session(session_id, context_updates):
    """
    Update session context after actions (cart, recommendations, payment, etc.).
    """
    result = sessions_collection.update_one(
        {"_id": session_id},
        {
            "$set": {
                "context": context_updates,
                "updated_at": datetime.utcnow()
            }
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
