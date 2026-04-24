from db.database import orders_collection
from agents.inventory_agent import InventoryAgent
from datetime import datetime
from bson import ObjectId


class FulfillmentAgent:

    @staticmethod
    def _serialize_item(item):
        return {
            **item,
            "product_id": str(item.get("product_id")) if item.get("product_id") is not None else None,
        }

    @staticmethod
    def process_order(order: dict):
        """
        Processes an order according to schema:
        - Deduct stock using InventoryAgent
        - Fills 'fulfillment' object as per schema
        - Sets order status: FULFILLED / PARTIALLY_FULFILLED / FAILED
        """
        fulfillment_type = order.get("fulfillment_type")
        store_location = order.get("store_location")
        order_id = order.get("order_id")
        if isinstance(order_id, str):
            order_id = ObjectId(order_id)

        existing_order = orders_collection.find_one({"_id": order_id}) if order_id else None
        inventory_state = (existing_order or {}).get("inventory") or {}

        if inventory_state.get("deducted"):
            fulfilled = [FulfillmentAgent._serialize_item(item) for item in order["items"]]
            unfulfilled = []
        else:
            deduction_result = InventoryAgent.deduct_order_stock(
                items=order.get("items", []),
                store_id=store_location
            )
            if deduction_result.get("success"):
                fulfilled = [FulfillmentAgent._serialize_item(item) for item in order["items"]]
                unfulfilled = []
                inventory_state = {
                    "deducted": True,
                    "deducted_at": datetime.utcnow(),
                    "allocations": deduction_result.get("allocations", []),
                }
            else:
                fulfilled = []
                unfulfilled = [FulfillmentAgent._serialize_item(item) for item in order["items"]]

        if not unfulfilled:
            status = "FULFILLED"
            success = True
            message = "All items fulfilled"
        elif fulfilled:
            status = "PARTIALLY_FULFILLED"
            success = False
            message = "Some items could not be fulfilled"
        else:
            status = "FAILED"
            success = False
            message = "No items fulfilled"

        update_doc = {
            "user_id": order["user_id"],
            "session_id": order.get("session_id"),
            "items": order["items"],
            "discounts_applied": order.get("discounts_applied", []),
            "final_price": order.get("final_price", 0),
            "payment": order.get("payment", {"status": "PENDING", "method": None, "transaction_id": None, "updated_at": None}),
            "fulfillment": {
                "type": fulfillment_type,
                "status": status
            },
            "inventory": inventory_state,
            "status": status.lower(),
            "confirmed_at": datetime.utcnow() if fulfilled else None
        }

        if order_id:
            orders_collection.update_one(
                {"_id": order_id},
                {
                    "$set": update_doc
                }
            )
            persisted_order_id = order_id
        else:
            order_doc = {
                **update_doc,
                "created_at": datetime.utcnow(),
            }
            persisted_order_id = orders_collection.insert_one(order_doc).inserted_id

        # Return a response with fulfillment details
        fulfillment_response = {
            "success": success,
            "order_id": persisted_order_id,
            "user_id": order["user_id"],
            "status": status,
            "fulfilled_items": fulfilled,
            "unfulfilled_items": unfulfilled,
            "fulfillment_type": fulfillment_type,
            "message": message
        }

        return fulfillment_response
