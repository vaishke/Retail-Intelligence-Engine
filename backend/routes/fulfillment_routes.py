from fastapi import APIRouter, Body
from services.fulfillment_service import FulfillmentService

router = APIRouter(
    prefix="/fulfillment",
    tags=["Fulfillment"]
)

@router.post("/create")
def create_fulfillment(data: dict = Body(...)):
    if not data.get("user_id") or not data.get("products"):
        return {
            "status": "error",
            "message": "user_id and products are required"
        }

    return FulfillmentService.create_fulfillment(data)
