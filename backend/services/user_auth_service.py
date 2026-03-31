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
            "user": {
                "user_id": str(user["_id"]),
                "name": user.get("name"),
                "email": user.get("email")
            }
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
                "user": {
                    "user_id": str(user["_id"]),
                    "name": user.get("name"),
                    "email": user.get("email")
                }
            }

        except jwt.ExpiredSignatureError:
            return {"success": False, "reason": "TOKEN_EXPIRED"}
        except jwt.InvalidTokenError:
            return {"success": False, "reason": "INVALID_TOKEN"}