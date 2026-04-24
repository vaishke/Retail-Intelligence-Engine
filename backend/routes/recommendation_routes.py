from typing import Optional

from fastapi import APIRouter, Body
from pydantic import BaseModel, Field

from services.recommendation_service import RecommendationService

router = APIRouter(tags=["Recommendation"])


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class EmbeddingBackfillRequest(BaseModel):
    batch_size: int = Field(default=50, ge=1, le=500)
    limit: Optional[int] = Field(default=None, ge=1)
    force: bool = False


class VectorIndexRequest(BaseModel):
    index_name: Optional[str] = None


@router.post("/recommendation/recommend")
async def recommend_products(data: dict = Body(...)):
    session_id = data.get("session_id")
    user_query = data.get("message") or data.get("user_query")

    if session_id and user_query:
        return await RecommendationService.recommend_with_memory_service(
            session_id=session_id,
            user_query=user_query,
            top_k=data.get("top_k", 5),
            exclude_product_ids=data.get("exclude_product_ids", []),
            additional_constraints=data.get("constraints", {}),
            persist_messages=bool(data.get("persist_messages", False)),
        )

    user_id = data.get("user_id")
    constraints = data.get("constraints", {})
    top_k = data.get("top_k", 5)
    exclude_product_ids = data.get("exclude_product_ids", [])

    if not user_id:
        return {
            "success": False,
            "reason": "MISSING_USER_ID",
            "recommendations": []
        }

    return RecommendationService.recommend_service(
        user_id=user_id,
        constraints=constraints,
        top_k=top_k,
        exclude_product_ids=exclude_product_ids
    )


@router.get("/recommend/similar/{product_id}")
@router.get("/recommendation/similar/{product_id}")
async def similar_products(product_id: str, top_k: int = 5):
    return await RecommendationService.similar_products_service(
        product_id=product_id,
        top_k=top_k,
    )


@router.post("/recommend/search")
@router.post("/recommendation/search")
async def semantic_search(payload: SemanticSearchRequest):
    return await RecommendationService.semantic_search_service(
        query=payload.query,
        top_k=payload.top_k,
    )


@router.post("/recommendation/admin/backfill-embeddings")
async def backfill_embeddings(payload: EmbeddingBackfillRequest):
    return await RecommendationService.backfill_embeddings_service(
        batch_size=payload.batch_size,
        limit=payload.limit,
        force=payload.force,
    )


@router.post("/recommendation/admin/create-vector-index")
async def create_vector_index(payload: VectorIndexRequest):
    return await RecommendationService.create_vector_index_service(
        index_name=payload.index_name,
    )
