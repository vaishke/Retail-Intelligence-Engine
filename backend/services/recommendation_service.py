from agents.recommendation_agent import RecommendationAgent
from fastapi.concurrency import run_in_threadpool

class RecommendationService:

    @staticmethod
    def recommend_service(user_id, constraints=None, top_k=5, exclude_product_ids=None):
        if not user_id:
            return {
                "success": False,
                "reason": "MISSING_USER_ID",
                "recommendations": []
            }

        input_json = {
            "user_id": user_id,
            "constraints": constraints or {},
            "top_k": top_k,
            "exclude_product_ids": exclude_product_ids or []
        }

        return RecommendationAgent.handle_request(input_json)

    @staticmethod
    async def semantic_search_service(query, top_k=5):
        return await run_in_threadpool(
            RecommendationAgent.semantic_search,
            query,
            top_k,
        )

    @staticmethod
    async def similar_products_service(product_id, top_k=5):
        return await run_in_threadpool(
            RecommendationAgent.similar_products,
            product_id,
            top_k,
        )

    @staticmethod
    async def backfill_embeddings_service(batch_size=50, limit=None, force=False):
        return await run_in_threadpool(
            RecommendationAgent.backfill_product_embeddings,
            batch_size,
            limit,
            force,
        )

    @staticmethod
    async def create_vector_index_service(index_name=None):
        return await run_in_threadpool(
            RecommendationAgent.create_vector_index,
            index_name,
        )

    @staticmethod
    async def recommend_with_memory_service(
        session_id,
        user_query,
        top_k=5,
        exclude_product_ids=None,
        additional_constraints=None,
        persist_messages=False,
    ):
        return await run_in_threadpool(
            RecommendationAgent.recommend_products_with_memory,
            session_id,
            user_query,
            top_k,
            exclude_product_ids,
            additional_constraints,
            persist_messages,
        )
