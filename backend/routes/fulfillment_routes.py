from fastapi import APIRouter, Body
from services.fulfillment_service import FulfillmentService

router = APIRouter(
    prefix="/fulfillment",
    tags=["Fulfillment"]
)

@router.post("/create")
def create_fulfillment(data: dict = Body(...)):
    return FulfillmentService.create_fulfillment(data)
