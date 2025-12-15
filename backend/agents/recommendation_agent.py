from db.database import users_collection, sessions_collection, products_collection


class RecommendationAgent:

    @staticmethod
    def recommend_products(user_id, session_id, constraints, top_k=5):
        user = users_collection.find_one({"_id": user_id})
        session = sessions_collection.find_one({"_id": session_id})

        if not user or not session:
            return {
                "status": "error",
                "message": "Invalid user or session"
            }

        query = RecommendationAgent._build_query(constraints, user)
        excluded = session.get("context", {}).get("selected_products", [])

        if excluded:
            query["_id"] = {"$nin": excluded}

        products = list(products_collection.find(query))

        if not products:
            return {
                "status": "no_results",
                "message": "No products found matching your preferences",
                "recommended_products": []
            }

        scored = RecommendationAgent._score_products(products, user)
        top_products = scored[:top_k]

        return {
            "status": "success",
            "recommended_products": top_products,
            "applied_filters": constraints
        }


    @staticmethod
    def _build_query(constraints, user):
        query = {}
        prefs = user.get("preferences", {})

        if constraints.get("category"):
            query["category"] = constraints["category"]

        if constraints.get("subcategory"):
            query["subcategory"] = constraints["subcategory"]

        price_range = constraints.get("price_range") or prefs.get("price_range")
        if price_range:
            query["price"] = {"$gte": price_range[0], "$lte": price_range[1]}

        if constraints.get("colors"):
            query["attributes.color"] = {"$in": constraints["colors"]}

        if constraints.get("styles"):
            query["tags"] = {"$in": constraints["styles"]}

        return query


    @staticmethod
    def _score_products(products, user):
        scored = []
        prefs = user.get("preferences", {})
        past_purchases = set(user.get("past_purchases", []))

        for product in products:
            score = 0
            signals = []

            if product.get("attributes", {}).get("color") in prefs.get("colors", []):
                score += 2
                signals.append("color_match")

            if set(product.get("tags", [])).intersection(set(prefs.get("styles", []))):
                score += 2
                signals.append("style_match")

            if product.get("_id") in past_purchases:
                score += 1
                signals.append("past_purchase")

            rating = product.get("ratings", 0)
            score += rating * 0.5
            if rating >= 4:
                signals.append("high_rating")

            scored.append({
                "product_id": product.get("_id"),
                "name": product.get("name"),
                "price": product.get("price"),
                "score": round(score, 2),
                "matched_signals": signals,
                "reason": RecommendationAgent._build_reason(signals)
            })

        return sorted(scored, key=lambda x: x["score"], reverse=True)


    @staticmethod
    def _build_reason(signals):
        if not signals:
            return "Popular product among users"
        return "Recommended based on your preferences"


    @staticmethod
    def handle_request(recommendation_request):
        action = recommendation_request.get("action")

        if action == "recommend":
            return RecommendationAgent.recommend_products(
                user_id=recommendation_request.get("user_id"),
                session_id=recommendation_request.get("session_id"),
                constraints=recommendation_request.get("constraints", {}),
                top_k=recommendation_request.get("top_k", 5)
            )

        return {
            "status": "error",
            "message": f"Invalid action '{action}'"
        }
