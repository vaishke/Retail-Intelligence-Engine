from fastapi import APIRouter, Body
from services.payment_service import PaymentService

router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)


@router.post("/process")
def process_payment(data: dict = Body(...)):
    return PaymentService.process_payment_service(data)
