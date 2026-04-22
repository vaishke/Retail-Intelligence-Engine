from __future__ import annotations

from datetime import datetime
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

from bson import ObjectId

from db.database import products_collection, sessions_collection, users_collection


class CartService:
    @staticmethod
    def get_cart(user_id: str) -> Dict[str, Any]:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return {"success": False, "message": "User not found", "cart": []}

        cart = user.get("cart", {"items": [], "total": 0})
        return {
            "success": True,
            "cart": CartService._serialize_cart_items(cart.get("items", [])),
            "total": cart.get("total", 0),
            "updated_at": cart.get("updated_at"),
        }

    @staticmethod
    def add_or_update_item(
        user_id: str,
        product_id: str,
        quantity: int,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        user_oid = ObjectId(user_id)
        product_oid = ObjectId(product_id)

        user = users_collection.find_one({"_id": user_oid})
        if not user:
            return {"success": False, "message": "User not found"}

        product = products_collection.find_one({"_id": product_oid})
        if not product:
            return {"success": False, "message": "Product not found"}

        existing_items = user.get("cart", {}).get("items", [])
        updated_items: List[Dict[str, Any]] = []
        found = False

        for item in existing_items:
            item_product_id = str(item.get("product_id"))
            if item_product_id == product_id:
                found = True
                if quantity > 0:
                    updated_items.append({
                        "product_id": product_oid,
                        "quantity": quantity,
                        "price": product.get("price", 0),
                        "name": product.get("name"),
                    })
            else:
                updated_items.append({
                    "product_id": item.get("product_id"),
                    "quantity": item.get("quantity", item.get("qty", 1)),
                    "price": item.get("price", 0),
                    "name": item.get("name"),
                })

        if not found and quantity > 0:
            updated_items.append({
                "product_id": product_oid,
                "quantity": quantity,
                "price": product.get("price", 0),
                "name": product.get("name"),
            })

        total = sum(item.get("price", 0) * item.get("quantity", 1) for item in updated_items)

        users_collection.update_one(
            {"_id": user_oid},
            {
                "$set": {
                    "cart.items": updated_items,
                    "cart.total": total,
                    "cart.updated_at": datetime.utcnow(),
                }
            },
        )

        serialized_items = CartService._serialize_cart_items(updated_items)

        if session_id:
            sessions_collection.update_one(
                {"_id": session_id},
                {
                    "$set": {
                        "context.selected_products": serialized_items,
                    },
                    "$currentDate": {"metadata.last_updated": True},
                },
            )

        return {
            "success": True,
            "cart": serialized_items,
            "total": total,
            "product": {
                "product_id": product_id,
                "name": product.get("name"),
                "price": product.get("price", 0),
            },
        }

    @staticmethod
    def resolve_product_reference(
        product_query: str,
        recommended_items: Optional[List[Dict[str, Any]]] = None,
        cart_items: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[Dict[str, Any]]:
        recommended_items = recommended_items or []
        cart_items = cart_items or []
        normalized_query = CartService._normalize_text(product_query)

        if not normalized_query or normalized_query in {"this", "that", "it", "recent item"}:
            if recommended_items:
                return recommended_items[0]
            return cart_items[-1] if cart_items else None

        candidates = recommended_items + cart_items
        best_candidate = None
        best_score = 0.0

        for candidate in candidates:
            candidate_name = CartService._normalize_text(candidate.get("name", ""))
            if not candidate_name:
                continue

            if normalized_query in candidate_name or candidate_name in normalized_query:
                return candidate

            score = SequenceMatcher(None, normalized_query, candidate_name).ratio()
            if score > best_score:
                best_score = score
                best_candidate = candidate

        if best_candidate and best_score >= 0.55:
            return best_candidate

        product_docs = list(products_collection.find({}, {"name": 1, "price": 1}).limit(200))
        best_product = None
        best_product_score = 0.0

        for product in product_docs:
            product_name = CartService._normalize_text(product.get("name", ""))
            if not product_name:
                continue

            if normalized_query in product_name or product_name in normalized_query:
                best_product = product
                best_product_score = 1.0
                break

            score = SequenceMatcher(None, normalized_query, product_name).ratio()
            if score > best_product_score:
                best_product_score = score
                best_product = product

        if best_product and best_product_score >= 0.6:
            return {
                "product_id": str(best_product["_id"]),
                "name": best_product.get("name"),
                "price": best_product.get("price", 0),
            }

        return None

    @staticmethod
    def _serialize_cart_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        serialized: List[Dict[str, Any]] = []
        for item in items:
            qty = item.get("qty", item.get("quantity", 1))
            serialized.append({
                "product_id": str(item.get("product_id")),
                "name": item.get("name"),
                "qty": qty,
                "quantity": qty,
                "price": item.get("price", 0),
            })
        return serialized

    @staticmethod
    def _normalize_text(value: str) -> str:
        return " ".join((value or "").lower().replace("-", " ").split())
