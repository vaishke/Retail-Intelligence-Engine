import unittest

from agents.recommendation_agent import RecommendationAgent


class RecommendationMatchingTests(unittest.TestCase):
    def test_indian_wear_query_prefers_ethnic_products_with_name_matches(self):
        products = [
            {
                "_id": "1",
                "name": "Women's Silk Saree",
                "category": "Clothing",
                "subcategory": "Ethnic Wear",
                "description": "Traditional festive saree for special occasions",
                "tags": ["ethnic", "festive", "women"],
                "ratings": 4.6,
                "images": [],
                "price": 4999,
            },
            {
                "_id": "2",
                "name": "Smart Home Hub Pro",
                "category": "Electronics",
                "subcategory": "Smart Devices",
                "description": "Control devices at home",
                "tags": ["smart", "home"],
                "ratings": 4.8,
                "images": [],
                "price": 5999,
            },
        ]

        ranked = RecommendationAgent._score_products(
            products,
            {
                "product_query": "indian wear",
                "subcategory": "Ethnic Wear",
                "category": "Clothing",
            },
        )

        self.assertEqual(ranked[0]["name"], "Women's Silk Saree")
        self.assertIn("SUBCATEGORY_MATCH", ranked[0]["signals"])
        self.assertGreater(ranked[0]["score"], ranked[1]["score"])

    def test_womens_clothing_query_uses_name_and_category_tokens(self):
        products = [
            {
                "_id": "1",
                "name": "Women's Cotton Kurti",
                "category": "Clothing",
                "subcategory": "Ethnic Wear",
                "description": "Everyday ethnic kurti",
                "tags": ["women", "ethnic", "casual"],
                "ratings": 4.2,
                "images": [],
                "price": 1499,
            },
            {
                "_id": "2",
                "name": "Men's Running Shoes",
                "category": "Footwear",
                "subcategory": "Sports",
                "description": "Lightweight trainers",
                "tags": ["men", "sports"],
                "ratings": 4.5,
                "images": [],
                "price": 2499,
            },
        ]

        ranked = RecommendationAgent._score_products(
            products,
            {
                "product_query": "women's clothing",
                "category": "Clothing",
            },
        )

        self.assertEqual(ranked[0]["name"], "Women's Cotton Kurti")
        self.assertIn("CATEGORY_MATCH", ranked[0]["signals"])
        self.assertTrue(
            any(signal in ranked[0]["signals"] for signal in ["TOKEN_MATCH", "SYNONYM_MATCH"])
        )

    def test_collect_text_terms_expands_ethnic_synonyms(self):
        terms = RecommendationAgent._collect_text_terms({"product_query": "indian wear"})

        self.assertIn("indian wear", terms)
        self.assertIn("ethnic wear", terms)
        self.assertIn("saree", terms)


if __name__ == "__main__":
    unittest.main()
