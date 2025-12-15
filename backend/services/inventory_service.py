from ..agents.inventory_agent import InventoryAgent

class InventoryService:
    
    @staticmethod
    def check_stock_service(sku, userLocation):
        input_json = {
                        "action": "check_stock",
                        "sku": sku,
                        "userLocation": userLocation
                    }
        return InventoryAgent.handle_request(input_json)
    
    @staticmethod
    def suggest_alternatives_service(category, budget):
        input_json = {
                        "action": "suggest_alternatives",
                        "category": category,
                        "budget": budget
                    }
        return InventoryAgent.handle_request(input_json)

    @staticmethod
    def get_store_stock_service(sku):
        input_json = {
                        "action": "get_store_stock",
                        "sku": sku
                    }
        return InventoryAgent.handle_request(input_json)
    
