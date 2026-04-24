import re
from difflib import SequenceMatcher
import os

from bson import ObjectId, Regex
from pymongo import DESCENDING

from services.recommendation_state_service import (
    build_missing_fields_prompt,
    build_recommendation_filters,
    build_recommendation_input,
    extract_state_updates,
    get_missing_recommendation_fields,
    has_recommendation_context,
    initialize_recommendation_state,
    merge_constraint_updates,
    merge_recommendation_state,
)
from services.session_service import (
    add_message,
    get_recommendation_state,
    get_session,
    save_recommendation_state,
)
from utils.embedding import EMBEDDING_DIMENSIONS, generate_embedding


class RecommendationAgent:
    VECTOR_INDEX_NAME = os.getenv("VECTOR_INDEX_NAME", "product_embedding_vector_index")
    VECTOR_NUM_CANDIDATES = int(os.getenv("VECTOR_NUM_CANDIDATES", "100"))
    STRONG_MATCH_THRESHOLD = float(os.getenv("VECTOR_STRONG_MATCH_THRESHOLD", "0.35"))
    QUERY_SYNONYMS = {
        "indian wear": ["ethnic wear", "traditional wear", "saree", "kurta", "kurti", "lehenga"],
        "ethnic wear": ["indian wear", "traditional wear", "saree", "kurta", "kurti", "lehenga"],
        "traditional wear": ["ethnic wear", "indian wear", "saree", "kurta", "kurti", "lehenga"],
        "women clothing": ["women", "clothing", "apparel", "dress", "kurti", "saree"],
        "womens clothing": ["women", "clothing", "apparel", "dress", "kurti", "saree"],
        "women s clothing": ["women", "clothing", "apparel", "dress", "kurti", "saree"],
        "clothes": ["clothing", "apparel"],
    }

    STOPWORDS = {
        "for", "and", "the", "with", "that", "this", "from", "into", "some", "any",
        "please", "show", "suggest", "recommend", "need", "want", "find", "give",
        "me", "wear", "shop", "shopping",
    }

    @staticmethod
    def recommend_products(user_id, constraints, top_k=5, exclude_product_ids=None):
        users_collection, products_collection = RecommendationAgent._get_collections()
        user_oid = user_id if isinstance(user_id, ObjectId) else ObjectId(user_id)
        user = users_collection.find_one({"_id": user_oid})

        if not user:
            return {
                "success": False,
                "reason": "INVALID_USER",
                "recommendations": []
            }

        query = RecommendationAgent._build_query(
            constraints,
            exclude_product_ids=exclude_product_ids,
        )

        # 🔍 DEBUG (keep this for now)
        print("FINAL QUERY:", query)

        products = list(products_collection.find(query).limit(200))

        if not products and RecommendationAgent._has_textual_intent(constraints):
            fallback_query = RecommendationAgent._build_query(
                constraints,
                use_text_filters=False,
                exclude_product_ids=exclude_product_ids,
            )
            products = list(products_collection.find(fallback_query).limit(300))

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
    def _build_query(constraints, use_text_filters=True, exclude_product_ids=None):
        query = {}

        if exclude_product_ids:
            exclude_oids = [
                ObjectId(pid) if not isinstance(pid, ObjectId) else pid
                for pid in exclude_product_ids
            ]
            query["_id"] = {"$nin": exclude_oids}

        if constraints.get("category"):
            query["category"] = {
                "$regex": f"^{constraints['category']}$",
                "$options": "i"
            }

        if constraints.get("subcategory"):
            query["subcategory"] = {
                "$regex": f"^{constraints['subcategory']}$",
                "$options": "i"
            }

        if constraints.get("tags"):
            query["tags"] = {
                "$in": [Regex(tag, "i") for tag in constraints["tags"]]
            }

        if constraints.get("price_range"):
            query["price"] = {
                "$gte": constraints["price_range"][0],
                "$lte": constraints["price_range"][1]
            }

        if constraints.get("colors"):
            query["attributes.color"] = {
                "$in": [Regex(color, "i") for color in constraints["colors"]]
            }

        if use_text_filters:
            text_terms = RecommendationAgent._collect_text_terms(constraints)
            if text_terms:
                regexes = [re.escape(term) for term in text_terms if term]
                query["$or"] = (
                    [{"name": {"$regex": term, "$options": "i"}} for term in regexes]
                    + [{"category": {"$regex": term, "$options": "i"}} for term in regexes]
                    + [{"subcategory": {"$regex": term, "$options": "i"}} for term in regexes]
                    + [{"description": {"$regex": term, "$options": "i"}} for term in regexes]
                    + [{"tags": {"$in": [Regex(term, "i")]}} for term in text_terms]
                )

        return query

    @staticmethod
    def _score_products(products, constraints):
        scored = []
        search_text = RecommendationAgent._normalize_text(constraints.get("product_query", ""))
        search_tokens = RecommendationAgent._meaningful_tokens(search_text)
        expanded_terms = RecommendationAgent._collect_text_terms(constraints)
        expanded_tokens = {
            token
            for term in expanded_terms
            for token in RecommendationAgent._meaningful_tokens(term)
        }

        for product in products:
            score = 0
            signals = []
            product_name = RecommendationAgent._normalize_text(product.get("name", ""))
            category = RecommendationAgent._normalize_text(product.get("category", ""))
            subcategory = RecommendationAgent._normalize_text(product.get("subcategory", ""))
            description = RecommendationAgent._normalize_text(product.get("description", ""))
            tag_values = [
                RecommendationAgent._normalize_text(tag)
                for tag in product.get("tags", [])
                if isinstance(tag, str)
            ]
            searchable_text = " ".join([product_name, category, subcategory, description, " ".join(tag_values)]).strip()

            if constraints.get("category") and category == RecommendationAgent._normalize_text(constraints["category"]):
                score += 4
                signals.append("CATEGORY_MATCH")

            if constraints.get("subcategory") and subcategory == RecommendationAgent._normalize_text(constraints["subcategory"]):
                score += 5
                signals.append("SUBCATEGORY_MATCH")

            if constraints.get("tags") and set(tag_values).intersection(
                RecommendationAgent._normalize_text(tag) for tag in constraints["tags"]
            ):
                score += 3
                signals.append("TAG_MATCH")

            if search_text:
                if search_text == product_name:
                    score += 12
                    signals.append("NAME_EXACT")
                elif search_text in product_name:
                    score += 9
                    signals.append("NAME_PARTIAL")
                elif search_text in subcategory or search_text in category:
                    score += 7
                    signals.append("CATEGORY_QUERY_MATCH")
                elif search_text in searchable_text:
                    score += 5
                    signals.append("TEXT_MATCH")

                token_hits = sum(1 for token in search_tokens if token in searchable_text)
                if token_hits:
                    score += min(6, token_hits * 2)
                    signals.append("TOKEN_MATCH")

                fuzzy_ratio = SequenceMatcher(None, search_text, product_name).ratio()
                if fuzzy_ratio >= 0.55:
                    score += round(fuzzy_ratio * 4, 2)
                    signals.append("FUZZY_NAME_MATCH")

            expanded_hits = sum(1 for token in expanded_tokens if token in searchable_text)
            if expanded_hits:
                score += min(4, expanded_hits)
                signals.append("SYNONYM_MATCH")

            rating = product.get("ratings", 0)
            score += round(rating * 0.75, 2)
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
                "reason": RecommendationAgent._build_reason(
                    signals=signals,
                    constraints=constraints,
                    product=product,
                )
            })

        return sorted(scored, key=lambda x: x["score"], reverse=True)

    @staticmethod
    def _build_reason(signals, constraints=None, product=None):
        constraints = constraints or {}
        product = product or {}
        if "NAME_EXACT" in signals or "NAME_PARTIAL" in signals:
            return f"Strong match for your search based on the product name: {product.get('name', 'this item')}."
        if "SUBCATEGORY_MATCH" in signals:
            return f"Fits the {constraints.get('subcategory', 'selected')} style you asked for."
        if "CATEGORY_MATCH" in signals and "TOKEN_MATCH" in signals:
            return f"Matches your search in {constraints.get('category', 'this category')} and aligns with your requested style."
        if "TAG_MATCH" in signals or "SYNONYM_MATCH" in signals:
            return "Matches related styles and keywords from your request."
        if "POPULAR" in signals:
            return "A popular, highly rated pick that shoppers often like."
        return "A relevant product pick based on your request."

    @staticmethod
    def _has_textual_intent(constraints):
        return bool(
            constraints.get("product_query")
            or constraints.get("subcategory")
            or constraints.get("tags")
        )

    @staticmethod
    def _collect_text_terms(constraints):
        terms = []
        for key in ("product_query", "subcategory", "category"):
            value = constraints.get(key)
            if isinstance(value, str) and value.strip():
                terms.append(RecommendationAgent._normalize_text(value))

        for tag in constraints.get("tags", []):
            if isinstance(tag, str) and tag.strip():
                terms.append(RecommendationAgent._normalize_text(tag))

        expanded = []
        for term in terms:
            expanded.append(term)
            expanded.extend(RecommendationAgent.QUERY_SYNONYMS.get(term, []))

        deduped = []
        seen = set()
        for term in expanded:
            normalized = RecommendationAgent._normalize_text(term)
            if normalized and normalized not in seen:
                deduped.append(normalized)
                seen.add(normalized)
        return deduped

    @staticmethod
    def _normalize_text(value):
        text = str(value or "").lower()
        text = text.replace("&", " and ")
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def _meaningful_tokens(value):
        return [
            token for token in RecommendationAgent._normalize_text(value).split()
            if len(token) > 1 and token not in RecommendationAgent.STOPWORDS
        ]

    @staticmethod
    def _get_collections():
        from db.database import users_collection, products_collection

        return users_collection, products_collection

    @staticmethod
    def _get_vector_collections():
        from db.database import db, inventory_collection, products_collection

        return db, products_collection, inventory_collection

    @staticmethod
    def _build_embedding_text(product):
        tags = product.get("tags", [])
        if isinstance(tags, list):
            tag_text = " ".join(str(tag).strip() for tag in tags if str(tag).strip())
        else:
            tag_text = str(tags or "").strip()

        fields = [
            product.get("name", ""),
            product.get("description", ""),
            tag_text,
            product.get("category", ""),
            product.get("subcategory", ""),
        ]
        return " ".join(str(field).strip() for field in fields if str(field).strip())

    @staticmethod
    def _get_or_create_embedding(product, persist=True):
        embedding = product.get("embedding")
        if isinstance(embedding, list) and len(embedding) == EMBEDDING_DIMENSIONS:
            return embedding

        product_text = RecommendationAgent._build_embedding_text(product)
        if not product_text:
            return None

        embedding = generate_embedding(product_text)
        if persist and product.get("_id"):
            _, products_collection, _ = RecommendationAgent._get_vector_collections()
            products_collection.update_one(
                {"_id": product["_id"]},
                {"$set": {"embedding": embedding}},
            )
        return embedding

    @staticmethod
    def _safe_rating(product):
        raw_rating = product.get("ratings", product.get("rating", 0)) or 0
        try:
            rating = float(raw_rating)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(5.0, rating))

    @staticmethod
    def _normalize_rating(product):
        return round(RecommendationAgent._safe_rating(product) / 5.0, 4)

    @staticmethod
    def _normalize_similarity(raw_score):
        try:
            similarity = float(raw_score or 0.0)
        except (TypeError, ValueError):
            return 0.0
        return round(max(0.0, min(1.0, similarity)), 4)

    @staticmethod
    def _stock_score(stock_total):
        if stock_total <= 0:
            return 0.0
        return round(min(stock_total / 10.0, 1.0), 4)

    @staticmethod
    def _inventory_totals_by_product(product_ids):
        if not product_ids:
            return {}

        _, _, inventory_collection = RecommendationAgent._get_vector_collections()
        pipeline = [
            {"$match": {"product_id": {"$in": product_ids}}},
            {"$group": {"_id": "$product_id", "totalStock": {"$sum": {"$ifNull": ["$quantity", 0]}}}},
        ]
        return {
            doc["_id"]: doc.get("totalStock", 0)
            for doc in inventory_collection.aggregate(pipeline)
        }

    @staticmethod
    def _resolve_stock_total(product, inventory_totals=None):
        inventory_totals = inventory_totals or {}
        product_id = product.get("_id")
        if product_id in inventory_totals:
            return inventory_totals[product_id]

        available_stores = product.get("available_stores", [])
        if isinstance(available_stores, list):
            total = 0
            for store in available_stores:
                if not isinstance(store, dict):
                    continue
                try:
                    total += int(store.get("stock", 0) or 0)
                except (TypeError, ValueError):
                    continue
            return total

        for key in ("stock", "quantity"):
            try:
                return max(0, int(product.get(key, 0) or 0))
            except (TypeError, ValueError):
                continue
        return 0

    @staticmethod
    def _calculate_final_score(similarity, product, inventory_totals=None):
        normalized_similarity = RecommendationAgent._normalize_similarity(similarity)
        normalized_rating = RecommendationAgent._normalize_rating(product)
        stock_total = RecommendationAgent._resolve_stock_total(product, inventory_totals)
        stock_score = RecommendationAgent._stock_score(stock_total)

        final_score = (
            (0.7 * normalized_similarity)
            + (0.2 * normalized_rating)
            + (0.1 * stock_score)
        )

        return {
            "similarity": normalized_similarity,
            "normalized_rating": normalized_rating,
            "stock_score": stock_score,
            "stock_total": stock_total,
            "final_score": round(final_score, 4),
        }

    @staticmethod
    def _format_vector_result(product, score_breakdown):
        return {
            "productId": str(product.get("_id")),
            "name": product.get("name"),
            "price": product.get("price"),
            "rating": RecommendationAgent._safe_rating(product),
            "similarityScore": score_breakdown["similarity"],
            "finalScore": score_breakdown["final_score"],
        }

    @staticmethod
    def _vector_search(query_vector, limit=5, exclude_product_ids=None, filters=None):
        _, products_collection, _ = RecommendationAgent._get_vector_collections()
        filters = filters or {}

        vector_stage = {
            "index": RecommendationAgent.VECTOR_INDEX_NAME,
            "path": "embedding",
            "queryVector": query_vector,
            "numCandidates": max(limit * 10, RecommendationAgent.VECTOR_NUM_CANDIDATES),
            "limit": max(limit * 3, limit),
        }
        if filters:
            vector_stage["filter"] = filters

        pipeline = [
            {"$vectorSearch": vector_stage},
            {
                "$project": {
                    "name": 1,
                    "price": 1,
                    "ratings": 1,
                    "rating": 1,
                    "available_stores": 1,
                    "stock": 1,
                    "quantity": 1,
                    "embedding": 1,
                    "score": {"$meta": "vectorSearchScore"},
                }
            },
        ]

        excluded = {
            product_id if isinstance(product_id, ObjectId) else ObjectId(product_id)
            for product_id in (exclude_product_ids or [])
        }

        results = []
        for product in products_collection.aggregate(pipeline):
            if product.get("_id") in excluded:
                continue
            results.append(product)
            if len(results) >= limit:
                break
        return results

    @staticmethod
    def _top_rated_fallback(top_k=5, exclude_product_ids=None, category=None):
        _, products_collection, _ = RecommendationAgent._get_vector_collections()
        query = {}
        if exclude_product_ids:
            query["_id"] = {
                "$nin": [
                    product_id if isinstance(product_id, ObjectId) else ObjectId(product_id)
                    for product_id in exclude_product_ids
                ]
            }
        if category:
            query["category"] = category

        fallback_products = list(
            products_collection.find(query).sort("ratings", DESCENDING).limit(top_k)
        )
        inventory_totals = RecommendationAgent._inventory_totals_by_product(
            [product["_id"] for product in fallback_products if product.get("_id")]
        )

        results = []
        for product in fallback_products:
            score_breakdown = RecommendationAgent._calculate_final_score(
                similarity=0.0,
                product=product,
                inventory_totals=inventory_totals,
            )
            results.append(RecommendationAgent._format_vector_result(product, score_breakdown))
        return results

    @staticmethod
    def semantic_search(query_text, top_k=5):
        if not query_text or not str(query_text).strip():
            return {
                "success": False,
                "reason": "MISSING_QUERY",
                "recommendations": [],
            }

        try:
            query_vector = generate_embedding(query_text)
        except RuntimeError as exc:
            return {
                "success": False,
                "reason": "EMBEDDING_MODEL_UNAVAILABLE",
                "message": str(exc),
                "recommendations": [],
            }
        vector_results = RecommendationAgent._vector_search(query_vector, limit=top_k)

        if not vector_results:
            return {
                "success": True,
                "recommendations": RecommendationAgent._top_rated_fallback(top_k=top_k),
                "fallbackUsed": True,
                "reason": "NO_VECTOR_MATCHES",
            }

        inventory_totals = RecommendationAgent._inventory_totals_by_product(
            [product["_id"] for product in vector_results if product.get("_id")]
        )

        ranked_results = []
        for product in vector_results:
            score_breakdown = RecommendationAgent._calculate_final_score(
                similarity=product.get("score", 0.0),
                product=product,
                inventory_totals=inventory_totals,
            )
            ranked_results.append({
                "product": product,
                "scores": score_breakdown,
            })

        ranked_results.sort(key=lambda item: item["scores"]["final_score"], reverse=True)
        formatted = [
            RecommendationAgent._format_vector_result(item["product"], item["scores"])
            for item in ranked_results[:top_k]
        ]

        best_similarity = max((item["scores"]["similarity"] for item in ranked_results), default=0.0)
        if best_similarity < RecommendationAgent.STRONG_MATCH_THRESHOLD:
            return {
                "success": True,
                "recommendations": RecommendationAgent._top_rated_fallback(top_k=top_k),
                "fallbackUsed": True,
                "reason": "LOW_VECTOR_CONFIDENCE",
            }

        return {
            "success": True,
            "recommendations": formatted,
            "fallbackUsed": False,
        }

    @staticmethod
    def similar_products(product_id, top_k=5):
        _, products_collection, _ = RecommendationAgent._get_vector_collections()
        product_oid = product_id if isinstance(product_id, ObjectId) else ObjectId(product_id)
        product = products_collection.find_one({"_id": product_oid})

        if not product:
            return {
                "success": False,
                "reason": "INVALID_PRODUCT",
                "recommendations": [],
            }

        try:
            query_vector = RecommendationAgent._get_or_create_embedding(product, persist=True)
        except RuntimeError as exc:
            return {
                "success": False,
                "reason": "EMBEDDING_MODEL_UNAVAILABLE",
                "message": str(exc),
                "recommendations": [],
            }
        if not query_vector:
            return {
                "success": False,
                "reason": "MISSING_PRODUCT_TEXT",
                "recommendations": [],
            }

        vector_results = RecommendationAgent._vector_search(
            query_vector,
            limit=top_k,
            exclude_product_ids=[product_oid],
        )

        if not vector_results:
            return {
                "success": True,
                "recommendations": RecommendationAgent._top_rated_fallback(
                    top_k=top_k,
                    exclude_product_ids=[product_oid],
                    category=product.get("category"),
                ),
                "fallbackUsed": True,
                "reason": "NO_SIMILAR_PRODUCTS",
            }

        inventory_totals = RecommendationAgent._inventory_totals_by_product(
            [doc["_id"] for doc in vector_results if doc.get("_id")]
        )

        ranked_results = []
        for similar_product in vector_results:
            score_breakdown = RecommendationAgent._calculate_final_score(
                similarity=similar_product.get("score", 0.0),
                product=similar_product,
                inventory_totals=inventory_totals,
            )
            ranked_results.append({
                "product": similar_product,
                "scores": score_breakdown,
            })

        ranked_results.sort(key=lambda item: item["scores"]["final_score"], reverse=True)

        return {
            "success": True,
            "sourceProductId": str(product_oid),
            "recommendations": [
                RecommendationAgent._format_vector_result(item["product"], item["scores"])
                for item in ranked_results[:top_k]
            ],
            "fallbackUsed": False,
        }

    @staticmethod
    def backfill_product_embeddings(batch_size=50, limit=None, force=False):
        _, products_collection, _ = RecommendationAgent._get_vector_collections()
        query = {}
        if not force:
            query["$or"] = [
                {"embedding": {"$exists": False}},
                {"embedding": []},
            ]

        cursor = products_collection.find(query).batch_size(max(1, batch_size))
        processed = 0
        updated = 0
        skipped = 0

        for product in cursor:
            if limit is not None and processed >= limit:
                break

            processed += 1
            product_text = RecommendationAgent._build_embedding_text(product)
            if not product_text:
                skipped += 1
                continue

            try:
                embedding = generate_embedding(product_text)
            except RuntimeError as exc:
                return {
                    "success": False,
                    "reason": "EMBEDDING_MODEL_UNAVAILABLE",
                    "message": str(exc),
                    "processed": processed,
                    "updated": updated,
                    "skipped": skipped,
                }
            products_collection.update_one(
                {"_id": product["_id"]},
                {"$set": {"embedding": embedding}},
            )
            updated += 1

        return {
            "success": True,
            "processed": processed,
            "updated": updated,
            "skipped": skipped,
            "dimensions": EMBEDDING_DIMENSIONS,
            "indexName": RecommendationAgent.VECTOR_INDEX_NAME,
        }

    @staticmethod
    def create_vector_index(index_name=None):
        db, _, _ = RecommendationAgent._get_vector_collections()
        target_index_name = index_name or RecommendationAgent.VECTOR_INDEX_NAME

        command = {
            "createSearchIndexes": "products",
            "indexes": [
                {
                    "name": target_index_name,
                    "type": "vectorSearch",
                    "definition": {
                        "fields": [
                            {
                                "type": "vector",
                                "path": "embedding",
                                "numDimensions": EMBEDDING_DIMENSIONS,
                                "similarity": "cosine",
                            }
                        ]
                    },
                }
            ],
        }

        result = db.command(command)
        return {
            "success": True,
            "indexName": target_index_name,
            "dimensions": EMBEDDING_DIMENSIONS,
            "similarity": "cosine",
            "result": result,
        }

    @staticmethod
    def recommend_products_with_memory(
        session_id,
        user_query,
        top_k=5,
        exclude_product_ids=None,
        additional_constraints=None,
        persist_messages=False,
    ):
        session = get_session(session_id)
        if not session:
            return {
                "success": False,
                "reason": "INVALID_SESSION",
                "recommendations": [],
            }

        current_state = get_recommendation_state(session_id)
        detected_updates = extract_state_updates(user_query)
        merged_state = merge_recommendation_state(current_state, detected_updates)
        merged_state = merge_constraint_updates(merged_state, additional_constraints)
        save_recommendation_state(session_id, merged_state)

        if persist_messages and user_query and user_query.strip():
            add_message(session_id, "user", user_query)

        missing_fields = get_missing_recommendation_fields(merged_state)
        filters = RecommendationAgent._merge_state_filters(
            state_filters=build_recommendation_filters(merged_state),
            additional_constraints=additional_constraints,
            user_query=user_query,
        )

        if missing_fields:
            response = {
                "success": True,
                "needs_clarification": True,
                "missing_fields": missing_fields,
                "message": build_missing_fields_prompt(missing_fields),
                "state": initialize_recommendation_state(merged_state),
                "filters": filters,
                "recommendation_input": build_recommendation_input(user_query, merged_state),
                "recommendations": [],
            }
            if persist_messages and response["message"]:
                add_message(session_id, "assistant", response["message"], payload=response)
            return response

        result = RecommendationAgent.recommend_products(
            user_id=session["user_id"],
            constraints=filters,
            top_k=top_k,
            exclude_product_ids=exclude_product_ids,
        )

        result["state"] = initialize_recommendation_state(merged_state)
        result["filters"] = filters
        result["recommendation_input"] = build_recommendation_input(user_query, merged_state)

        if result.get("success"):
            RecommendationAgent._save_last_recommendations(session_id, result.get("recommendations", []))
            if persist_messages and result.get("recommendations"):
                add_message(
                    session_id,
                    "assistant",
                    f"Recommended {len(result.get('recommendations', []))} product(s).",
                    payload=result,
                )
        return result

    @staticmethod
    def _merge_state_filters(state_filters, additional_constraints=None, user_query=""):
        merged = dict(additional_constraints or {})
        state_filters = dict(state_filters or {})

        if state_filters.get("category"):
            merged["category"] = state_filters["category"]

        if state_filters.get("price_range"):
            merged["price_range"] = state_filters["price_range"]

        combined_tags = []
        for tag in merged.get("tags", []):
            if isinstance(tag, str) and tag.strip():
                combined_tags.append(tag.strip())
        for tag in state_filters.get("tags", []):
            if isinstance(tag, str) and tag.strip():
                combined_tags.append(tag.strip())
        if combined_tags:
            merged["tags"] = list(dict.fromkeys(combined_tags))

        if state_filters.get("subcategory") and not merged.get("subcategory"):
            merged["subcategory"] = state_filters["subcategory"]

        effective_product_query = RecommendationAgent._resolve_effective_product_query(
            user_query=user_query,
            merged_constraints=merged,
            state_filters=state_filters,
        )
        if effective_product_query:
            merged["product_query"] = effective_product_query

        return merged

    @staticmethod
    def _resolve_effective_product_query(user_query="", merged_constraints=None, state_filters=None):
        merged_constraints = merged_constraints or {}
        state_filters = state_filters or {}

        stored_query = state_filters.get("product_query")
        current_query = str(user_query or "").strip()
        normalized_current = current_query.lower()

        looks_like_follow_up = bool(current_query) and not any(
            token in normalized_current
            for token in ["show", "recommend", "suggest", "find", "looking for", "need", "want", "browse"]
        )

        if looks_like_follow_up:
            slot_only_updates = extract_state_updates(current_query)
            if slot_only_updates and has_recommendation_context(state_filters):
                return stored_query or merged_constraints.get("product_query")

        if merged_constraints.get("product_query"):
            return merged_constraints["product_query"]

        if current_query:
            return current_query

        return stored_query or merged_constraints.get("product_query")

    @staticmethod
    def _save_last_recommendations(session_id, recommendations):
        session = get_session(session_id)
        if not session:
            return

        context = session.get("context", {})
        context["last_recommendations"] = recommendations
        context["recommendations"] = recommendations
        save_recommendation_state(session_id, context.get("recommendation_state"))
        from db.database import sessions_collection

        sessions_collection.update_one(
            {"_id": session_id},
            {
                "$set": {
                    "context.last_recommendations": recommendations,
                    "context.recommendations": recommendations,
                },
                "$currentDate": {"metadata.last_updated": True}
            }
        )

    @staticmethod
    def handle_request(recommendation_request):
        return RecommendationAgent.recommend_products(
            user_id=recommendation_request.get("user_id"),
            constraints=recommendation_request.get("constraints", {}),
            top_k=recommendation_request.get("top_k", 5),
            exclude_product_ids=recommendation_request.get("exclude_product_ids", [])
        )
