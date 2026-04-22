from bson import ObjectId, Regex
from db.database import users_collection, products_collection
import re


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
        top_k = max(1, min(int(top_k or 5), 10))

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
            for k in ["category", "subcategory", "tags", "price_range", "product_query", "colors"]
            if k in constraints
        }

        return {
            "success": True,
            "recommendations": top_products,
            "applied_filters": applied_filters
        }

    @staticmethod
    def _build_query(constraints):
        and_filters = []
        text_clauses = []

        # Case-insensitive category match
        if constraints.get("category"):
            text_clauses.append({"category": {"$regex": f"^{re.escape(constraints['category'])}$", "$options": "i"}})

        # Case-insensitive subcategory match
        if constraints.get("subcategory"):
            text_clauses.append({"subcategory": {"$regex": f"^{re.escape(constraints['subcategory'])}$", "$options": "i"}})

        # Case-insensitive tag match
        if constraints.get("tags"):
            text_clauses.append({"tags": {"$in": [Regex(tag, "i") for tag in constraints["tags"]]}})

        if constraints.get("product_query"):
            product_query = constraints["product_query"].strip()
            phrase_regex = Regex(re.escape(product_query), "i")
            text_clauses.extend([
                {"name": phrase_regex},
                {"description": phrase_regex},
                {"subcategory": phrase_regex},
                {"category": phrase_regex},
                {"tags": {"$in": [phrase_regex]}}
            ])

        # Price range filter
        if constraints.get("price_range"):
            and_filters.append({
                "price": {
                    "$gte": constraints["price_range"][0],
                    "$lte": constraints["price_range"][1]
                }
            })

        # Color filter
        if constraints.get("colors"):
            and_filters.append({"attributes.color": {"$in": constraints["colors"]}})

        if text_clauses:
            and_filters.append({"$or": text_clauses})

        if not and_filters:
            return {}

        if len(and_filters) == 1:
            return and_filters[0]

        return {"$and": and_filters}

    @staticmethod
    def _score_products(products, constraints):
        scored = []
        product_query = (constraints.get("product_query") or "").strip().lower()
        query_tokens = [token for token in re.findall(r"\w+", product_query) if len(token) > 1]

        for product in products:
            score = 0.0
            signals = []
            name = (product.get("name") or "").lower()
            description = (product.get("description") or "").lower()
            category = (product.get("category") or "").lower()
            subcategory = (product.get("subcategory") or "").lower()
            tags = [tag.lower() for tag in product.get("tags", [])]
            color = str(product.get("attributes", {}).get("color", "")).lower()

            if product_query and product_query in name:
                score += 12
                signals.append("NAME_MATCH")

            if product_query and product_query in description:
                score += 8
                signals.append("DESCRIPTION_MATCH")

            token_hits = 0
            for token in query_tokens:
                if token in name:
                    token_hits += 1
                elif token in description or token in subcategory or token in category or token in tags:
                    token_hits += 0.75

            if token_hits:
                score += token_hits * 3
                signals.append("QUERY_MATCH")

            # Category/Subcategory/Tag scoring
            if constraints.get("category") and category == constraints["category"].lower():
                score += 5
                signals.append("CATEGORY_MATCH")

            if constraints.get("subcategory") and subcategory == constraints["subcategory"].lower():
                score += 4
                signals.append("SUBCATEGORY_MATCH")

            if constraints.get("tags") and set(tags).intersection(
                map(str.lower, constraints["tags"])
            ):
                score += 3
                signals.append("TAG_MATCH")

            if constraints.get("colors") and color in [c.lower() for c in constraints["colors"]]:
                score += 2
                signals.append("COLOR_MATCH")

            # Popularity
            rating = product.get("ratings", 0)
            score += min(rating, 5) * 0.3
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
                "signals": list(dict.fromkeys(signals)),
                "reason": RecommendationAgent._build_reason(signals)
            })

        return sorted(scored, key=lambda x: x["score"], reverse=True)

    @staticmethod
    def _build_reason(signals):
        unique_signals = list(dict.fromkeys(signals))

        if not unique_signals:
            return "Popular product among users"

        reason_map = {
            "NAME_MATCH": "Matched your requested product",
            "DESCRIPTION_MATCH": "Description closely matches your query",
            "QUERY_MATCH": "Relevant to your search terms",
            "CATEGORY_MATCH": "Matches your selected category",
            "SUBCATEGORY_MATCH": "Matches your selected style",
            "TAG_MATCH": "Matches your preferred attributes",
            "COLOR_MATCH": "Matches your selected color",
            "POPULAR": "Popular among users",
        }

        reasons = [reason_map[signal] for signal in unique_signals if signal in reason_map]
        if not reasons:
            return "Popular product among users"

        return ", ".join(reasons[:2])

    @staticmethod
    def handle_request(recommendation_request):
        return RecommendationAgent.recommend_products(
            user_id=recommendation_request.get("user_id"),
            constraints=recommendation_request.get("constraints", {}),
            top_k=recommendation_request.get("top_k", 5),
            exclude_product_ids=recommendation_request.get("exclude_product_ids", [])
        )
