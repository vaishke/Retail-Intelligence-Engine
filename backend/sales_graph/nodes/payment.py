from services.payment_service import PaymentService
from sales_graph.state import SalesState


def payment_node(state: SalesState) -> SalesState:
    order_id = state.get("order_id")
    payment_method = state.get("payment_method")

    if not order_id or not payment_method:
        return {
            **state,
            "last_step": "PAYMENT_PENDING"
        }

    result = PaymentService.process_payment_service({
        "order_id": order_id,
        "payment_method": payment_method
    })

    return {
        **state,
        "payment": result,
        "last_step": "PAYMENT_DONE" if result.get("success") else "PAYMENT_FAILED"
    }
