from db.database import inventory_collection, products_collection


class InventoryAgent:

    @staticmethod
    def check_stock(product_id, userLocation=None):
        records = list(inventory_collection.find({"product_id": str(product_id)}))

        if not records:
            return {
                "success": False,
                "reason": "NOT_FOUND",
                "product_id": product_id,
                "isAvailable": False
            }

        total_quantity = sum(r.get("quantity", 0) for r in records)

        location_quantity = 0
        if userLocation:
            location_quantity = sum(
                r.get("quantity", 0) for r in records if r.get("store_id") == userLocation
            )

        product = products_collection.find_one({"_id": product_id})
        product_name = product.get("name") if product else ""

        return {
            "success": True,
            "product_id": product_id,
            "productName": product_name,
            "totalStock": total_quantity,
            "locationStock": location_quantity,
            "isAvailable": total_quantity > 0
        }

    @staticmethod
    def get_store_stock(product_id):
        records = list(inventory_collection.find({"product_id": str(product_id)}))

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

        product = products_collection.find_one({"_id": product_id})
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
                userLocation=inventory_request.get("userLocation")
            )

        elif action == "get_store_stock":
            return InventoryAgent.get_store_stock(
                product_id=inventory_request.get("product_id")
            )

        else:
            return {
                "success": False,
                "reason": f"INVALID_ACTION: {action}"
            }