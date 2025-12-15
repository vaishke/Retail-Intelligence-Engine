from agents.recommendation_agent import RecommendationAgent

class RecommendationService:

    @staticmethod
    def recommend_service(user_id, session_id, constraints=None, top_k=5):
        if not user_id or not session_id:
            return {
                "status": "error",
                "message": "user_id and session_id are required"
            }

        input_json = {
            "action": "recommend",
            "user_id": user_id,
            "session_id": session_id,
            "constraints": constraints or {},
            "top_k": top_k
        }

        return RecommendationAgent.handle_request(input_json)
