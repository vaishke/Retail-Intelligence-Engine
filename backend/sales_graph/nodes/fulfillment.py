from services.fulfillment_service import FulfillmentService
from sales_graph.state import SalesState


def fulfillment_node(state):
    order_payload = {
        "user_id": state["user_id"],
        "products": state.get("cart_items") or state.get("recommendations", []),
        "address": state.get("delivery_address", {})
    }

    result = FulfillmentService.create_fulfillment(order_payload)

    return {
        **state,
        "fulfillment_result": result,
        "last_step": "FULFILLMENT_CREATED"
    }
