import os
import bcrypt
import jwt
from datetime import datetime, timedelta
from bson import ObjectId
from db.database import users_collection

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
TOKEN_EXPIRY_MINUTES = 60 * 24   # 1 day


class UserAuthService:

    @staticmethod
    def register_user(name, email, password):
        existing_user = users_collection.find_one({"email": email})
        if existing_user:
            return {
                "success": False,
                "reason": "USER_ALREADY_EXISTS"
            }

        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        user = {
            "name": name,
            "email": email,
            "password_hash": password_hash,
            "created_at": datetime.utcnow(),

            "gender": None,
            "location": None,

            "preferences": {
                "styles": [],
                "colors": [],
                "price_range": []
            },

            "loyalty": {
                "tier": "Bronze",
                "points": 0
            },

            "past_purchases": [],
            "payment_methods": []
        }

        result = users_collection.insert_one(user)

        return {
            "success": True,
            "user_id": str(result.inserted_id)
        }

    @staticmethod
    def login_user(email, password):
        user = users_collection.find_one({"email": email})
        if not user:
            return {
                "success": False,
                "reason": "USER_NOT_FOUND"
            }

        if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            return {
                "success": False,
                "reason": "INVALID_PASSWORD"
            }

        token_data = {
            "user_id": str(user["_id"]),
            "exp": datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRY_MINUTES)
        }

        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

        return {
            "success": True,
            "token": token,
            "user": UserAuthService._serialize_user(user)
        }

    @staticmethod
    def get_current_user(token):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("user_id")

            user = users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                return {"success": False, "reason": "USER_NOT_FOUND"}

            return {
                "success": True,
                "user": UserAuthService._serialize_user(user)
            }

        except jwt.ExpiredSignatureError:
            return {"success": False, "reason": "TOKEN_EXPIRED"}
        except jwt.InvalidTokenError:
            return {"success": False, "reason": "INVALID_TOKEN"}

    @staticmethod
    def _serialize_user(user):
        loyalty = user.get("loyalty", {})
        return {
            "user_id": str(user["_id"]),
            "name": user.get("name"),
            "email": user.get("email"),
            "loyalty": {
                "tier": loyalty.get("tier", "Bronze"),
                "points": loyalty.get("points", 0),
            },
            "loyaltyPoints": loyalty.get("points", 0),
            "memberSince": user.get("created_at"),
            "created_at": user.get("created_at"),
            "past_purchases": user.get("past_purchases", []),
            "payment_methods": user.get("payment_methods", []),
        }
    
def verify_token(token: str):
    print("TOKEN RECEIVED:", token)

    result = UserAuthService.get_current_user(token)

    print("DECODE RESULT:", result)

    if not result["success"]:
        return None

    return result["user"]
