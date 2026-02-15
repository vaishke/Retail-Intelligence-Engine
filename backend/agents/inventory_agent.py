from pymongo import ReturnDocument
from bson import ObjectId
from db.database import inventory_collection, products_collection


class InventoryAgent:

    @staticmethod
    def check_stock(product_id, store_id=None):
        product_oid = ObjectId(product_id)
        records = list(inventory_collection.find({"product_id": product_oid}))

        if not records:
            return {
                "success": False,
                "reason": "NOT_FOUND",
                "product_id": product_id,
                "isAvailable": False
            }

        total_quantity = sum(r.get("quantity", 0) for r in records)

        location_quantity = 0
        if store_id:
            location_quantity = sum(
                r.get("quantity", 0) for r in records if r.get("store_id") == store_id
            )

        product = products_collection.find_one({"_id": product_oid})
        product_name = product.get("name") if product else ""

        return {
            "success": True,
            "product_id": product_id,
            "productName": product_name,
            "totalStock": total_quantity,
            "storeStock": location_quantity,
            "isAvailable": total_quantity > 0
        }

    @staticmethod
    def deduct_stock(product_id, store_id, quantity):
        product_oid = ObjectId(product_id)
        updated_record = inventory_collection.find_one_and_update(
            {
                "product_id": product_oid,
                "store_id": store_id,
                "quantity": {"$gte": quantity}
            },
            {"$inc": {"quantity": -quantity}, "$set": {"last_updated": datetime.utcnow()}},
            return_document=ReturnDocument.AFTER
        )

        if not updated_record:
            return {
                "success": False,
                "reason": "INSUFFICIENT_STOCK_OR_NOT_FOUND",
                "product_id": product_id,
                "store_id": store_id
            }

        # Recalculate total stock after deduction
        total_quantity = sum(
            r.get("quantity", 0)
            for r in inventory_collection.find({"product_id": product_oid})
        )

        return {
            "success": True,
            "product_id": product_id,
            "store_id": store_id,
            "deducted": quantity,
            "remainingStoreStock": updated_record.get("quantity", 0),
            "totalStock": total_quantity,
            "isAvailable": total_quantity > 0
        }

    @staticmethod
    def get_store_stock(product_id):
        product_oid = ObjectId(product_id)
        records = list(inventory_collection.find({"product_id": product_oid}))

        if not records:
            return {
                "success": False,
                "reason": "NOT_FOUND",
                "product_id": product_id,
                "isAvailable": False
            }

        store_stock = {
            r["store_id"]: r.get("quantity", 0)
            for r in records
        }

        total_quantity = sum(store_stock.values())

        product = products_collection.find_one({"_id": product_oid})
        product_name = product.get("name") if product else ""

        return {
            "success": True,
            "product_id": product_id,
            "productName": product_name,
            "storeStock": store_stock,
            "totalStock": total_quantity,
            "isAvailable": total_quantity > 0
        }

    @staticmethod
    def handle_request(inventory_request):
        action = inventory_request.get("action")

        if action == "check_stock":
            return InventoryAgent.check_stock(
                product_id=inventory_request.get("product_id"),
                store_id=inventory_request.get("store_id")
            )

        elif action == "get_store_stock":
            return InventoryAgent.get_store_stock(
                product_id=inventory_request.get("product_id")
            )

        elif action == "deduct_stock":
            return InventoryAgent.deduct_stock(
                product_id=inventory_request.get("product_id"),
                store_id=inventory_request.get("store_id"),
                quantity=inventory_request.get("quantity", 1)
            )

        else:
            return {
                "success": False,
                "reason": f"INVALID_ACTION: {action}"
            }