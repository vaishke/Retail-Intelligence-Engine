
from ..db.database import inventory_collection
class InventoryAgent:

    @staticmethod
    def check_stock(sku, userLocation):
        record = inventory_collection.find_one({"sku": sku})
        if not record:
            return {
                "status": "not_found",
                "message": f"No product found for SKU {sku}",
                "isAvailable": False
            }
        online_stock = record.get("availableOnline", 0)
        store_stock = record.get("storeStock", {}).get(userLocation, 0)
        total_stock = online_stock + store_stock

        if total_stock > 0:
            return {
                "status" : "success",
                "sku": sku,
                "productName": record.get("productName", ""),
                "availableOnline": online_stock,
                "storeStock": record.get("storeStock", {}),
                "isAvailable": True
            }
        else:
            alternatives = InventoryAgent.suggest_alternatives(record.get("category"), record.get("price", 0))
            if alternatives:
                return alternatives
            return {
                "status": "out_of_stock",
                "sku": sku,
                "productName": record.get("productName", ""),
                "message": "Item is currently unavailable.",
                "isAvailable": False
            }
    @staticmethod
    def suggest_alternatives(category, budget):

        record = inventory_collection.find({"category": category})

        alternatives = []

        for product in record:
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
                "status": "success",
                "category": category,
                "budget": budget,
                "alternatives": top_alternatives,
                "message": f"Found {len(top_alternatives)} alternative(s).",
                "isAvailable": True
            }
        else:
            return {
                "status": "no_alternatives",
                "category": category,
                "budget": budget,
                "alternatives": [],
                "message": "No suitable alternatives found.",
                "isAvailable": False
            }
        
    @staticmethod
    def get_store_stock(sku):

        record = inventory_collection.find_one({"sku": sku})
        if not record:
            return {
                "status": "not_found",
                "message": f"No product found for SKU {sku}",
                "isAvailable": False
            }
        store_stock = record.get("storeStock", {})
        online_stock = record.get("availableOnline", 0)

        return {
            "status": "success",
            "sku": sku,
            "productName": record.get("productName", ""),
            "availableOnline": online_stock,
            "storeStock": store_stock,
            "isAvailable": (online_stock + sum(store_stock.values())) > 0
        }
    
    @staticmethod
    def handle_request(inventory_request):

        action = inventory_request.get("action")

        if action == "check_stock":
            sku = inventory_request.get("sku")
            userLocation = inventory_request.get("userLocation")

            if not sku or not userLocation:
                return {"status": "error", "message": "sku and userLocation required"}

            return InventoryAgent.check_stock(sku, userLocation)

        elif action == "suggest_alternatives":
            category = inventory_request.get("category")
            budget = inventory_request.get("budget")

            if not category or budget is None:
                return {"status": "error", "message": "category and budget required"}

            return InventoryAgent.suggest_alternatives(category, budget)

        elif action == "get_store_stock":
            sku = inventory_request.get("sku")

            if not sku:
                return {"status": "error", "message": "sku required"}

            return InventoryAgent.get_store_stock(sku)

        else:
            return {
                "status": "error",
                "message": f"Invalid action '{action}'"
            }
