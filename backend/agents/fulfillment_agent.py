from db.database import orders_collection
from agents.inventory_agent import InventoryAgent
from datetime import datetime
from bson import ObjectId


class FulfillmentAgent:

    @staticmethod
    def process_order(order: dict):
        """
        Processes an order according to schema:
        - Deduct stock using InventoryAgent
        - Fills 'fulfillment' object as per schema
        - Sets order status: FULFILLED / PARTIALLY_FULFILLED / FAILED
        """

        fulfilled = []
        unfulfilled = []

        fulfillment_type = order.get("fulfillment_type")
        store_location = order.get("store_location")

        for item in order["items"]:
            product_id = item["product_id"]
            qty = item["qty"]

            target_store = store_location

            # If no store specified, pick any store with enough stock
            if not target_store:
                store_stock = InventoryAgent.get_store_stock(product_id)
                if not store_stock.get("success"):
                    unfulfilled.append(item)
                    continue

                found_store = None
                for store_id, stock_qty in store_stock["storeStock"].items():
                    if stock_qty >= qty:
                        found_store = store_id
                        break

                if not found_store:
                    unfulfilled.append(item)
                    continue

                target_store = found_store

            deduction = InventoryAgent.deduct_stock(
                product_id=product_id,
                store_id=target_store,
                quantity=qty
            )

            if deduction.get("success"):
                fulfilled.append(item)
            else:
                unfulfilled.append(item)

        # Determine overall order status
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

        order_id = order.get("order_id")
        if isinstance(order_id, str):
            order_id = ObjectId(order_id)
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
