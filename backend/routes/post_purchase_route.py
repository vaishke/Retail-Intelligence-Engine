from services.post_purchase_service import PostPurchaseService

from fastapi import APIRouter, Body

router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"]
)

@router.post("/postpurchase")
def complete_post_purchase(data: dict = Body(...)):
    return PostPurchaseService.handle_post_service(data)