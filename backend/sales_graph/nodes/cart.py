from sales_graph.state import SalesState


def cart_node(state: SalesState) -> SalesState:
    selected_sku = state.get("selected_sku")

    if not selected_sku:
        return {
            **state,
            "last_step": "CART_NO_SELECTION"
        }

    cart = state.get("cart_items", [])
    cart.append({
        "sku": selected_sku,
        "quantity": 1
    })

    return {
        **state,
        "cart_items": cart,
        "last_step": "CART_UPDATED"
    }
