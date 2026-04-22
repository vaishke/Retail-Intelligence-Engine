from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from services.order_service import OrderService
from services.user_auth_service import verify_token


router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)):
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


@router.post("")
def place_order(data: dict = Body(...)):
    result = OrderService.place_order(data)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result)
    return result


@router.get("")
def get_my_orders(user=Depends(get_current_user)):
    result = OrderService.list_orders_for_user(user["user_id"])
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to fetch orders"))
    return result
