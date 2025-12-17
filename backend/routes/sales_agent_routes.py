from fastapi import APIRouter, Body
from services.session_service import create_session, get_session, update_session, end_session
from services.recommendation_service import RecommendationService
from services.inventory_service import InventoryService
from services.offer_loyalty_service import OfferLoyaltyService
from services.payment_service import PaymentService
from services.post_purchase_service import PostPurchaseService
from sales_graph.graph import build_sales_graph

router = APIRouter(
    prefix="/sales",
    tags=["Sales Agent"]
)

sales_app = build_sales_graph()

@router.post("/chat")
def sales_chat(payload: dict = Body(...)):
    """
    Unified entry point for the Sales Agent.
    Drives the LangGraph workflow.
    """

    if "user_id" not in payload:
        return {
            "success": False,
            "message": "user_id is required"
        }

    result = sales_app.invoke(payload)

    return {
        "success": True,
        "state": result
    }

@router.post("/session/start")
def start_session(data: dict = Body(...)):
    user_id = data.get("user_id")
    channel = data.get("channel", "WEB")
    return create_session(user_id, channel)

@router.get("/session/{session_id}")
def get_session_route(session_id: str):
    return get_session(session_id)

@router.post("/session/update/{session_id}")
def update_session_route(session_id: str, data: dict = Body(...)):
    return update_session(session_id, data)

@router.post("/session/end/{session_id}")
def end_session_route(session_id: str):
    return {"success": end_session(session_id)}

@router.post("/recommend/{session_id}")
def recommend(session_id: str, data: dict = Body(...)):
    session = get_session(session_id)
    constraints = data.get("constraints", {})
    exclude_products = session["context"].get("selected_products", [])
    recs = RecommendationService.recommend_service(
        user_id=session["user_id"],
        constraints=constraints,
        top_k=data.get("top_k", 5),
        exclude_product_ids=exclude_products
    )
    session["context"]["recommendations"] = recs
    update_session(session_id, session["context"])
    return recs

@router.post("/inventory/{session_id}")
def check_inventory(session_id: str, data: dict = Body(...)):
    session = get_session(session_id)
    user_location = data.get("user_location")
    stock_results = [
        InventoryService.check_stock_service(sku, user_location)
        for sku in session["context"].get("selected_products", [])
    ]
    session["context"]["stock_status"] = stock_results
    update_session(session_id, session["context"])
    return stock_results

@router.post("/offers/{session_id}")
def apply_offers(session_id: str, data: dict = Body(...)):
    session = get_session(session_id)
    cart_items = data.get("cart_items", [])
    coupon = data.get("coupon_code")
    use_points = data.get("use_points", 0)
    offers = OfferLoyaltyService.checkout_service(session["user_id"], cart_items, coupon, use_points)
    session["context"]["offers_applied"] = offers
    update_session(session_id, session["context"])
    return offers

@router.post("/payment/{session_id}")
def process_payment(session_id: str, data: dict = Body(...)):
    session = get_session(session_id)
    payment_data = {
        "order_id": session["context"].get("cart_order_id"),
        "payment_method": data.get("payment_method"),
        "details": data.get("details", {})
    }
    payment_result = PaymentService.process_payment_service(payment_data)
    session["context"]["payment_status"] = payment_result.get("success")
    session["context"]["transaction_id"] = payment_result.get("transaction_id")
    update_session(session_id, session["context"])
    return payment_result

@router.post("/post_purchase/{session_id}")
def post_purchase(session_id: str, data: dict = Body(...)):
    session = get_session(session_id)
    post_data = {
        "order_id": session["context"].get("cart_order_id"),
        "transaction_id": session["context"].get("transaction_id"),
        "user_id": session["user_id"],
        "cart_items": data.get("cart_items", []),
        "final_amount": data.get("final_amount"),
        "delivery_address": data.get("delivery_address")
    }
    result = PostPurchaseService.handle_post_service(post_data)
    end_session(session_id)
    return result
