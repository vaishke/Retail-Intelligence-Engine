from agents.fulfillment_agent import FulfillmentAgent
import uuid
from datetime import datetime

class FulfillmentService:

    @staticmethod
    def create_fulfillment(data: dict):
        # Validate required fields
        required_fields = ["user_id", "products", "fulfillment_type"]
        missing = [f for f in required_fields if f not in data]
        if missing:
            return {
                "success": False,
                "order_id": "",
                "user_id": data.get("user_id", ""),
                "message": f"Missing required fields: {', '.join(missing)}"
            }

        # Generate order_id
        order_id = "ORD-" + str(uuid.uuid4())[:8].upper()

        # Build payload for agent
        fulfillment_request = {
            "order_id": order_id,
            "user_id": data["user_id"],
            "products": data["products"],
            "fulfillment_type": data["fulfillment_type"],
            "store_location": data.get("store_location"),
            "delivery_address": data.get("delivery_address"),
            "created_at": datetime.utcnow().isoformat()
        }

        # Delegate execution to agent
        return FulfillmentAgent.process_order(fulfillment_request)
