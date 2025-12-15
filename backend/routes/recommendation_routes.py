from fastapi import APIRouter, Body
from services.recommendation_service import RecommendationService

router = APIRouter(
    prefix="/recommendation",
    tags=["Recommendation"]
)


@router.post("/recommend")
def recommend_products(data: dict = Body(...)):
    user_id = data.get("user_id")
    session_id = data.get("session_id")
    constraints = data.get("constraints", {})
    top_k = data.get("top_k", 5)

    if not user_id or not session_id:
        return {
            "status": "error",
            "message": "user_id and session_id are required"
        }

    return RecommendationService.recommend_service(
        user_id=user_id,
        session_id=session_id,
        constraints=constraints,
        top_k=top_k
    )
