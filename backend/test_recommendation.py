from services.recommendation_service import RecommendationService

TEST_USER_ID = "test_user_001"
TEST_SESSION_ID = "test_session_001"

def run_test():
    constraints = {
        "category": "Apparel",
        "price_range": [500, 2500],
        "colors": ["black", "blue"]
    }

    response = RecommendationService.recommend_service(
        user_id=TEST_USER_ID,
        session_id=TEST_SESSION_ID,
        constraints=constraints,
        top_k=3
    )

    print("\n=== Recommendation Service Output ===")
    print(response)


if __name__ == "__main__":
    run_test()
