from services.inventory_service import InventoryService
from sales_graph.state import SalesState


def inventory_node(state: SalesState) -> SalesState:
    recommendations = state.get("recommendations", [])
    user_location = state.get("user_location")

    if not recommendations:
        return {
            **state,
            "last_step": "INVENTORY_SKIPPED"
        }

    inventory_results = []

    for product in recommendations:
        sku = product.get("product_id")
        stock = InventoryService.check_stock_service(sku, user_location)
        inventory_results.append({
            "sku": sku,
            "stock": stock
        })

    return {
        **state,
        "inventory_status": inventory_results,
        "last_step": "INVENTORY_CHECKED"
    }
