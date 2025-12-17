from db.database import inventory_collection


class InventoryAgent:

    @staticmethod
    def check_stock(sku, userLocation):
        record = inventory_collection.find_one({"sku": sku})
        if not record:
            return {
                "success": False,
                "reason": "NOT_FOUND",
                "sku": sku,
                "productName": "",
                "isAvailable": False
            }

        online_stock = record.get("availableOnline", 0)
        store_stock = record.get("storeStock", {}).get(userLocation, 0)
        total_stock = online_stock + store_stock

        if total_stock > 0:
            return {
                "success": True,
                "sku": sku,
                "productName": record.get("productName", ""),
                "availableOnline": online_stock,
                "storeStock": record.get("storeStock", {}),
                "isAvailable": True
            }
        else:
            alternatives = InventoryAgent.suggest_alternatives(record.get("category"), record.get("price", 0))
            if alternatives.get("success"):
                return alternatives
            return {
                "success": False,
                "reason": "OUT_OF_STOCK",
                "sku": sku,
                "productName": record.get("productName", ""),
                "isAvailable": False,
                "message": "Item is currently unavailable."
            }

    @staticmethod
    def suggest_alternatives(category, budget):
        cursor = inventory_collection.find({"category": category})
        alternatives = []

        for product in cursor:
            price = product.get("price", 0)
            online_stock = product.get("availableOnline", 0)
            if online_stock > 0 and price <= budget * 1.2:
                alternatives.append({
                    "sku": product.get("sku", ""),
                    "productName": product.get("productName", ""),
                    "price": price,
                    "availableOnline": online_stock
                })

        alternatives.sort(key=lambda x: x["price"])
        top_alternatives = alternatives[:3]

        if top_alternatives:
            return {
                "success": True,
                "category": category,
                "budget": budget,
                "alternatives": top_alternatives,
                "isAvailable": True,
                "message": f"Found {len(top_alternatives)} alternative(s)."
            }
        else:
            return {
                "success": False,
                "reason": "NO_ALTERNATIVES",
                "category": category,
                "budget": budget,
                "alternatives": [],
                "isAvailable": False,
                "message": "No suitable alternatives found."
            }

    @staticmethod
    def get_store_stock(sku):
        record = inventory_collection.find_one({"sku": sku})
        if not record:
            return {
                "success": False,
                "reason": "NOT_FOUND",
                "sku": sku,
                "productName": "",
                "isAvailable": False
            }

        store_stock = record.get("storeStock", {})
        online_stock = record.get("availableOnline", 0)
        total_available = online_stock + sum(store_stock.values())

        return {
            "success": True,
            "sku": sku,
            "productName": record.get("productName", ""),
            "availableOnline": online_stock,
            "storeStock": store_stock,
            "isAvailable": total_available > 0
        }

    @staticmethod
    def handle_request(inventory_request):
        action = inventory_request.get("action")

        if action == "check_stock":
            return InventoryAgent.check_stock(
                sku=inventory_request.get("sku"),
                userLocation=inventory_request.get("userLocation")
            )
        elif action == "suggest_alternatives":
            return InventoryAgent.suggest_alternatives(
                category=inventory_request.get("category"),
                budget=inventory_request.get("budget")
            )
        elif action == "get_store_stock":
            return InventoryAgent.get_store_stock(
                sku=inventory_request.get("sku")
            )
        else:
            return {
                "success": False,
                "reason": f"INVALID_ACTION: {action}"
            }
