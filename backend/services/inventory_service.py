from agents.inventory_agent import InventoryAgent


class InventoryService:

    @staticmethod
    def check_stock_service(sku, userLocation):
        if not sku or not userLocation:
            return {
                "success": False,
                "reason": "MISSING_PARAMETERS",
                "sku": sku or "",
                "isAvailable": False
            }

        input_json = {
            "action": "check_stock",
            "sku": sku,
            "userLocation": userLocation
        }
        return InventoryAgent.handle_request(input_json)

    @staticmethod
    def suggest_alternatives_service(category, budget):
        if not category or budget is None:
            return {
                "success": False,
                "reason": "MISSING_PARAMETERS",
                "category": category or "",
                "budget": budget or 0,
                "alternatives": [],
                "isAvailable": False
            }

        input_json = {
            "action": "suggest_alternatives",
            "category": category,
            "budget": budget
        }
        return InventoryAgent.handle_request(input_json)

    @staticmethod
    def get_store_stock_service(sku):
        if not sku:
            return {
                "success": False,
                "reason": "MISSING_PARAMETERS",
                "sku": "",
                "isAvailable": False
            }

        input_json = {
            "action": "get_store_stock",
            "sku": sku
        }
        return InventoryAgent.handle_request(input_json)
