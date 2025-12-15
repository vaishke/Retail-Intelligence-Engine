from fastapi import APIRouter, Body
from services.offer_loyalty_service import OfferLoyaltyService

router = APIRouter(
    prefix="/offers",
    tags=["Offers & Loyalty"]
)

@router.post("/checkout")
def checkout(data: dict = Body(...)):
    user_id = data.get("user_id")
    cart_items = data.get("cart_items")
    coupon_code = data.get("coupon_code")
    use_points = data.get("use_points", 0)

    if not user_id or not cart_items:
        return {
            "success": False,
            "message": "user_id and cart_items are required"
        }

    return OfferLoyaltyService.checkout_service(
        user_id, cart_items, coupon_code, use_points
    )


@router.get("/loyalty/{user_id}")
def get_loyalty_status(user_id: str):
    return OfferLoyaltyService.get_loyalty_status_service(user_id)


@router.get("/active")
def get_active_offers():
    return OfferLoyaltyService.view_offers_service()
