from fastapi import APIRouter, Body
from services.payment_service import PaymentService

router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)

@router.post("/process")
def process_payment(data: dict = Body(...)):
    required_fields = ["order_id", "payment_method"]
    missing = [f for f in required_fields if f not in data]

    if missing:
        return {
            "status": "error",
            "message": f"Missing fields: {', '.join(missing)}"
        }

    return PaymentService.process_payment_service(data)
