from db.database import users_collection, products_collection


class RecommendationAgent:

    @staticmethod
    def recommend_products(user_id, constraints, top_k=5, exclude_product_ids=None):
        user = users_collection.find_one({"_id": user_id})

        if not user:
            return {
                "success": False,
                "reason": "INVALID_USER",
                "recommendations": []
            }

        query = RecommendationAgent._build_query(constraints)

        if exclude_product_ids:
            query["_id"] = {"$nin": exclude_product_ids}

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
            for k in ["category", "subcategory", "price_range"]
            if k in constraints
        }

        return {
            "success": True,
            "recommendations": top_products,
            "applied_filters": applied_filters
        }

    @staticmethod
    def _build_query(constraints):
        query = {}
        if constraints.get("category"):
            query["category"] = constraints["category"]

        if constraints.get("subcategory"):
            query["subcategory"] = constraints["subcategory"]

        if constraints.get("price_range"):
            query["price"] = {"$gte": constraints["price_range"][0],
                              "$lte": constraints["price_range"][1]}

        if constraints.get("colors"):
            query["attributes.color"] = {"$in": constraints["colors"]}

        if constraints.get("tags"):
            query["tags"] = {"$in": constraints["tags"]}

        return query

    @staticmethod
    def _score_products(products, constraints):
        scored = []

        for product in products:
            score = 0
            signals = []

            # Category/Subcategory match
            if product.get("category") == constraints.get("category"):
                score += 3
                signals.append("CATEGORY_MATCH")

            if product.get("subcategory") == constraints.get("subcategory"):
                score += 2
                signals.append("SUBCATEGORY_MATCH")

            # Tag match
            if set(product.get("tags", [])).intersection(set(constraints.get("tags", []))):
                score += 2
                signals.append("TAG_MATCH")

            # Popularity (rating)
            rating = product.get("rating", 0)
            score += rating
            if rating >= 4:
                signals.append("POPULAR")

            scored.append({
                "product_id": product.get("_id"),
                "name": product.get("name"),
                "category": product.get("category"),
                "subcategory": product.get("subcategory"),
                "price": product.get("price"),
                "rating": rating,
                "image": product.get("image"),
                "score": round(score, 2),
                "signals": signals,
                "reason": RecommendationAgent._build_reason(signals)
            })

        return sorted(scored, key=lambda x: x["score"], reverse=True)

    @staticmethod
    def _build_reason(signals):
        if not signals:
            return "Popular product among users"
        return "Matches your selected category and budget"

    @staticmethod
    def handle_request(recommendation_request):
        return RecommendationAgent.recommend_products(
            user_id=recommendation_request.get("user_id"),
            constraints=recommendation_request.get("constraints", {}),
            top_k=recommendation_request.get("top_k", 5),
            exclude_product_ids=recommendation_request.get("exclude_product_ids", [])
        )
