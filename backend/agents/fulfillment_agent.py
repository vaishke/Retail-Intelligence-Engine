from backend.db.database import orders_collection, products_collection
from datetime import datetime

class FulfillmentAgent:

    @staticmethod
    def process_order(order: dict):
        """
        Handles:
        - SHIP_TO_HOME
        - CLICK_AND_COLLECT
        - RESERVE_IN_STORE
        """

        fulfilled = []
        unfulfilled = []

        fulfillment_type = order.get("fulfillment_type")
        store_location = order.get("store_location")

        for item in order["products"]:
            product = products_collection.find_one({"sku": item["sku"]})

            if not product:
                unfulfilled.append(item)
                continue

            available_stock = product.get("stock", 0)

            if available_stock >= item["quantity"]:
                fulfilled.append(item)
                # Deduct stock
                products_collection.update_one(
                    {"sku": item["sku"]},
                    {"$inc": {"stock": -item["quantity"]}}
                )
            else:
                unfulfilled.append(item)

        # Determine order status
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
            message = "Fulfillment failed"

        # Build fulfillment response
        fulfillment_response = {
            "success": success,
            "order_id": order["order_id"],
            "user_id": order["user_id"],
            "status": status,
            "fulfilled_products": fulfilled,
            "unfulfilled_products": unfulfilled,
            "fulfillment_type": fulfillment_type,
            "message": message
        }

        # Add conditional fields based on fulfillment type
        if fulfillment_type == "SHIP_TO_HOME":
            fulfillment_response["delivery_status"] = "Scheduled"
        elif fulfillment_type == "CLICK_AND_COLLECT":
            fulfillment_response["pickup_store"] = store_location
            fulfillment_response["pickup_status"] = "Ready for pickup"
        elif fulfillment_type == "RESERVE_IN_STORE":
            fulfillment_response["reservation_store"] = store_location
            fulfillment_response["reservation_status"] = "Reserved"

        # Save order
        orders_collection.insert_one({
            **fulfillment_response,
            "created_at": datetime.utcnow()
        })

        return fulfillment_response
