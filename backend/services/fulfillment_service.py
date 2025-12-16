from agents.fulfillment_agent import FulfillmentAgent
from datetime import datetime
import uuid


class FulfillmentService:
    """
    Orchestrates fulfillment workflows:
    - Ship to Home
    - Click & Collect
    - Reserve in Store
    """

    @staticmethod
    def create_fulfillment(order_data: dict):
        """
        order_data example:
        {
            "user_id": "U123",
            "products": [
                {"sku": "SHOE001", "quantity": 1, "price": 2999}
            ],
            "fulfillment_type": "CLICK_AND_COLLECT",
            "store_location": "Hyderabad",
            "delivery_address": {
                "line1": "Flat 101",
                "city": "Hyderabad",
                "pincode": "500081"
            }
        }
        """

        # 1️⃣ Generate Order ID
        order_id = "ORD-" + str(uuid.uuid4())[:8].upper()

        # 2️⃣ Build orchestration payload
        fulfillment_request = {
            "order_id": order_id,
            "user_id": order_data.get("user_id"),
            "products": order_data.get("products", []),
            "fulfillment_type": order_data.get("fulfillment_type"),
            "store_location": order_data.get("store_location"),
            "delivery_address": order_data.get("delivery_address"),
            "created_at": datetime.utcnow().isoformat()
        }

        # 3️⃣ Delegate execution to Agent
        return FulfillmentAgent.process_order(fulfillment_request)
