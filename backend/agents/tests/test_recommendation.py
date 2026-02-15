from pprint import pprint

from agents.recommendation_agent import RecommendationAgent
from db.database import users_collection


def get_test_user():
    user = users_collection.find_one({"name": "Lalitha"})
    if not user:
        raise Exception("Test user 'Lalitha' not found in DB")
    return user


def main():
    user = get_test_user()
    user_id = user["_id"]

    print(f"\nTesting recommendations for user: {user['name']} (ID: {user_id})\n")

    constraints = {
        "category": "Clothing",
        "subcategory": "Ethnic Wear",
        "price_range": [0, 100000],
        "colors": user.get("preferences", {}).get("colors", []),
        "tags": []
    }

    recommendation_request = {
        "user_id": user_id,
        "constraints": constraints,
        "top_k": 5,
        "exclude_product_ids": []
    }

    result = RecommendationAgent.handle_request(recommendation_request)

    print("=== Recommendation Result ===")
    pprint(result)

    if result["success"]:
        print("\nTop Recommended Products:\n")
        for idx, product in enumerate(result["recommendations"], start=1):
            print(f"{idx}. {product['name']}")
            print(f"   Category: {product['category']} > {product['subcategory']}")
            print(f"   Price: ₹{product['price']}")
            print(f"   Rating: {product['rating']}")
            print(f"   Score: {product['score']}")
            print(f"   Signals: {product['signals']}")
            print(f"   Reason: {product['reason']}\n")
    else:
        print("No recommendations found. Reason:", result["reason"])


if __name__ == "__main__":
    main()