from services.offer_loyalty_service import OfferLoyaltyService
from sales_graph.state import SalesState


def offers_node(state: SalesState) -> SalesState:
    user_id = state.get("user_id")
    cart_items = state.get("cart_items", [])

    if not cart_items:
        return {
            **state,
            "last_step": "OFFERS_SKIPPED"
        }

    result = OfferLoyaltyService.checkout_service(
        user_id=user_id,
        cart_items=cart_items
    )

    return {
        **state,
        "pricing": result,
        "last_step": "OFFERS_APPLIED"
    }
