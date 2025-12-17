from agents.recommendation_agent import RecommendationAgent

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
