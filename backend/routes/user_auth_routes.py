from fastapi import APIRouter, Body, Header
from services.user_auth_service import UserAuthService

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


@router.post("/register")
def register(data: dict = Body(...)):
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not all([name, email, password]):
        return {
            "success": True,
            "token": token,
            "user": user
        }

    return UserAuthService.register_user(name, email, password)


@router.post("/login")
def login(data: dict = Body(...)):
    email = data.get("email")
    password = data.get("password")

    if not all([email, password]):
        return {
            "success": False,
            "reason": "MISSING_FIELDS"
        }

    return UserAuthService.login_user(email, password)


@router.get("/me")
def get_me(authorization: str = Header(None)):
    if not authorization:
        return {
            "success": False,
            "reason": "MISSING_TOKEN"
        }

    try:
        token = authorization.split(" ")[1]  # "Bearer <token>"
    except:
        return {
            "success": False,
            "reason": "INVALID_AUTH_HEADER"
        }

    return UserAuthService.get_current_user(token)