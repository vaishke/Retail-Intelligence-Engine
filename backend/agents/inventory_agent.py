from pymongo import ReturnDocument
from bson import ObjectId
from db.database import inventory_collection, products_collection
from datetime import datetime


class InventoryAgent:

    @staticmethod
    def _normalize_product_id(product_id):
        return product_id if isinstance(product_id, ObjectId) else ObjectId(product_id)

    @staticmethod
    def check_stock(product_id, store_id=None):
        product_oid = InventoryAgent._normalize_product_id(product_id)
        records = list(inventory_collection.find({"product_id": product_oid}))

        if not records:
            return {
                "success": False,
                "reason": "NOT_FOUND",
                "product_id": product_id,
                "isAvailable": False,
                "requestedQuantity": max(int(quantity or 1), 1),
                "availableQuantity": 0,
            }

        requested_quantity = max(int(quantity or 1), 1)
        total_quantity = sum(r.get("quantity", 0) for r in records)

        location_quantity = 0
        if store_id:
            location_quantity = sum(
                r.get("quantity", 0) for r in records if r.get("store_id") == store_id
            )

        product = products_collection.find_one({"_id": product_oid})
        product_name = product.get("name") if product else ""
        available_quantity = location_quantity if store_id else total_quantity

        return {
            "success": True,
            "product_id": product_id,
            "productName": product_name,
            "totalStock": total_quantity,
            "storeStock": location_quantity,
            "requestedQuantity": requested_quantity,
            "availableQuantity": available_quantity,
            "isAvailable": available_quantity >= requested_quantity,
        }

    @staticmethod
    def deduct_stock(product_id, store_id, quantity):
        product_oid = InventoryAgent._normalize_product_id(product_id)
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
        product_oid = InventoryAgent._normalize_product_id(product_id)
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
    def restore_stock(product_id, store_id, quantity):
        product_oid = InventoryAgent._normalize_product_id(product_id)
        inventory_collection.update_one(
            {"product_id": product_oid, "store_id": store_id},
            {"$inc": {"quantity": quantity}, "$set": {"last_updated": datetime.utcnow()}}
        )

    @staticmethod
    def deduct_order_stock(items, store_id=None):
        allocations = []

        for item in items or []:
            product_id = item.get("product_id")
            qty = int(item.get("qty", item.get("quantity", 1)))

            if not product_id or qty <= 0:
                InventoryAgent._rollback_allocations(allocations)
                return {
                    "success": False,
                    "reason": "INVALID_ORDER_ITEM",
                    "allocations": allocations,
                }

            target_store = store_id
            if not target_store:
                store_stock = InventoryAgent.get_store_stock(product_id)
                if not store_stock.get("success"):
                    InventoryAgent._rollback_allocations(allocations)
                    return {
                        "success": False,
                        "reason": store_stock.get("reason", "STORE_STOCK_LOOKUP_FAILED"),
                        "product_id": str(product_id),
                        "allocations": allocations,
                    }

                for candidate_store, stock_qty in store_stock.get("storeStock", {}).items():
                    if stock_qty >= qty:
                        target_store = candidate_store
                        break

            if not target_store:
                InventoryAgent._rollback_allocations(allocations)
                return {
                    "success": False,
                    "reason": "INSUFFICIENT_STOCK_OR_NOT_FOUND",
                    "product_id": str(product_id),
                    "allocations": allocations,
                }

            deduction = InventoryAgent.deduct_stock(product_id, target_store, qty)
            if not deduction.get("success"):
                InventoryAgent._rollback_allocations(allocations)
                return {
                    "success": False,
                    "reason": deduction.get("reason", "INSUFFICIENT_STOCK_OR_NOT_FOUND"),
                    "product_id": str(product_id),
                    "store_id": target_store,
                    "allocations": allocations,
                }

            allocations.append(
                {
                    "product_id": str(InventoryAgent._normalize_product_id(product_id)),
                    "qty": qty,
                    "store_id": target_store,
                }
            )

        return {
            "success": True,
            "allocations": allocations,
        }

    @staticmethod
    def _rollback_allocations(allocations):
        for allocation in reversed(allocations):
            InventoryAgent.restore_stock(
                product_id=allocation["product_id"],
                store_id=allocation["store_id"],
                quantity=allocation["qty"],
            )

    @staticmethod
    def handle_request(inventory_request):
        action = inventory_request.get("action")

        if action == "check_stock":
            return InventoryAgent.check_stock(
                product_id=inventory_request.get("product_id"),
                store_id=inventory_request.get("store_id"),
                quantity=inventory_request.get("quantity", 1),
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
