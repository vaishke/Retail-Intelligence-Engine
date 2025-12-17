from services.recommendation_service import RecommendationService
from sales_graph.state import SalesState


def recommendation_node(state: SalesState) -> SalesState:
    user_id = state.get("user_id")
    constraints = state.get("constraints", {})

    if not user_id:
        return {
            **state,
            "error": "MISSING_USER_ID",
            "last_step": "RECOMMENDATION_FAILED"
        }

    response = RecommendationService.recommend_service(
        user_id=user_id,
        constraints=constraints
    )

    if not response.get("success"):
        return {
            **state,
            "recommendations": [],
            "last_step": "RECOMMENDATION_NO_RESULTS"
        }

    return {
        **state,
        "recommendations": response.get("recommendations", []),
        "last_step": "RECOMMENDATION_DONE"
    }
