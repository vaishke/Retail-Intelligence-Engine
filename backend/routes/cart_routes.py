from fastapi import APIRouter, Body, HTTPException

from services.cart_service import CartService


router = APIRouter(
    prefix="/cart",
    tags=["Cart"]
)


@router.get("/{user_id}")
def get_cart(user_id: str):
    result = CartService.get_cart(user_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message", "Cart not found"))
    return result


@router.post("/add")
def add_to_cart(data: dict = Body(...)):
    user_id = data.get("user_id")
    product_id = data.get("product_id")
    quantity = int(data.get("quantity", 1))
    session_id = data.get("session_id")

    if not user_id or not product_id:
        raise HTTPException(status_code=400, detail="user_id and product_id are required")

    result = CartService.add_or_update_item(
        user_id=user_id,
        product_id=product_id,
        quantity=quantity,
        session_id=session_id,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to update cart"))

    return result
