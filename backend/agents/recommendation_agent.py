from bson import ObjectId, Regex
from db.database import users_collection, products_collection


class RecommendationAgent:

    @staticmethod
    def recommend_products(user_id, constraints, top_k=5, exclude_product_ids=None):
        user_oid = ObjectId(user_id)
        user = users_collection.find_one({"_id": user_oid})

        if not user:
            return {
                "success": False,
                "reason": "INVALID_USER",
                "recommendations": []
            }

        query = RecommendationAgent._build_query(constraints)

        if exclude_product_ids:
            exclude_oids = [ObjectId(pid) if not isinstance(pid, ObjectId) else pid for pid in exclude_product_ids]
            query["_id"] = {"$nin": exclude_oids}

        products = list(products_collection.find(query))

        if not products:
            return {
                "success": False,
                "reason": "NO_MATCHING_PRODUCTS",
                "recommendations": []
            }

        scored = RecommendationAgent._score_products(products, constraints)
        top_products = scored[:top_k]

        applied_filters = {
            k: constraints[k]
            for k in ["category", "subcategory", "tags", "price_range"]
            if k in constraints
        }

        return {
            "success": True,
            "recommendations": top_products,
            "applied_filters": applied_filters
        }

    @staticmethod
    def _build_query(constraints):
        query = {"$or": []}

        # Case-insensitive category match
        if constraints.get("category"):
            query["$or"].append({"category": {"$regex": f"^{constraints['category']}$", "$options": "i"}})

        # Case-insensitive subcategory match
        if constraints.get("subcategory"):
            query["$or"].append({"subcategory": {"$regex": f"^{constraints['subcategory']}$", "$options": "i"}})

        # Case-insensitive tag match
        if constraints.get("tags"):
            query["$or"].append({"tags": {"$in": [Regex(tag, "i") for tag in constraints["tags"]]}})

        # Price range filter
        if constraints.get("price_range"):
            query["price"] = {
                "$gte": constraints["price_range"][0],
                "$lte": constraints["price_range"][1]
            }

        # Color filter
        if constraints.get("colors"):
            query["attributes.color"] = {"$in": constraints["colors"]}

        # If no $or conditions, remove it to avoid empty $or
        if not query["$or"]:
            query.pop("$or")

        return query

    @staticmethod
    def _score_products(products, constraints):
        scored = []

        for product in products:
            score = 0
            signals = []

            # Category/Subcategory/Tag scoring
            if constraints.get("category") and product.get("category", "").lower() == constraints["category"].lower():
                score += 3
                signals.append("CATEGORY_MATCH")

            if constraints.get("subcategory") and product.get("subcategory", "").lower() == constraints["subcategory"].lower():
                score += 2
                signals.append("SUBCATEGORY_MATCH")

            if constraints.get("tags") and set(map(str.lower, product.get("tags", []))).intersection(
                map(str.lower, constraints["tags"])
            ):
                score += 2
                signals.append("TAG_MATCH")

            # Popularity
            rating = product.get("ratings", 0)
            score += rating
            if rating >= 4:
                signals.append("POPULAR")

            scored.append({
                "product_id": str(product.get("_id")),
                "name": product.get("name"),
                "category": product.get("category"),
                "subcategory": product.get("subcategory"),
                "price": product.get("price"),
                "ratings": rating,
                "image": product.get("images")[0] if product.get("images") else None,
                "score": round(score, 2),
                "signals": signals,
                "reason": RecommendationAgent._build_reason(signals)
            })

        return sorted(scored, key=lambda x: x["score"], reverse=True)

    @staticmethod
    def _build_reason(signals):
        if not signals:
            return "Popular product among users"
        return "Matches your selected category, subcategory, or tags"

    @staticmethod
    def handle_request(recommendation_request):
        return RecommendationAgent.recommend_products(
            user_id=recommendation_request.get("user_id"),
            constraints=recommendation_request.get("constraints", {}),
            top_k=recommendation_request.get("top_k", 5),
            exclude_product_ids=recommendation_request.get("exclude_product_ids", [])
        )