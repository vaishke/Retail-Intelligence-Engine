from services.post_purchase_service import PostPurchaseService
from sales_graph.state import SalesState


def post_purchase_node(state: SalesState) -> SalesState:
    input_json = {
        "order_id": state.get("order_id"),
        "transaction_id": state.get("payment", {}).get("transaction_id"),
        "user_id": state.get("user_id"),
        "cart_items": state.get("cart_items"),
        "final_amount": state.get("pricing", {}).get("final_amount"),
        "delivery_address": state.get("delivery_address")
    }

    result = PostPurchaseService.handle_post_service(input_json)

    return {
        **state,
        "post_purchase": result,
        "last_step": "SESSION_COMPLETED"
    }
