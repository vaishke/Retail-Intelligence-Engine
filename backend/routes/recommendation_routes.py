from fastapi import APIRouter, Body
from services.recommendation_service import RecommendationService

router = APIRouter(
    prefix="/recommendation",
    tags=["Recommendation"]
)


@router.post("/recommend")
def recommend_products(data: dict = Body(...)):
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