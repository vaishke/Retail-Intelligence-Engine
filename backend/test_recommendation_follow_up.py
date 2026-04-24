import unittest
from unittest.mock import patch
import sys
import types

from sales_graph.nodes.intent_detector import intent_detector_node
from services.recommendation_state_service import get_missing_recommendation_fields


sentence_transformers_stub = types.ModuleType("sentence_transformers")


class _DummySentenceTransformer:
    def __init__(self, *args, **kwargs):
        pass


sentence_transformers_stub.SentenceTransformer = _DummySentenceTransformer
sys.modules.setdefault("sentence_transformers", sentence_transformers_stub)

from agents.recommendation_agent import RecommendationAgent


class RecommendationFollowUpTests(unittest.TestCase):
    def test_product_context_counts_as_known_category_for_missing_fields(self):
        missing_fields = get_missing_recommendation_fields(
            {
                "product_query": "ethnic wear",
                "subcategory": "Ethnic Wear",
                "tags": ["ethnic"],
            }
        )

        self.assertEqual(missing_fields, ["price", "occasion"])

    def test_slot_only_follow_up_preserves_original_product_query(self):
        filters = RecommendationAgent._merge_state_filters(
            state_filters={
                "product_query": "ethnic wear",
                "subcategory": "Ethnic Wear",
                "tags": ["ethnic"],
            },
            additional_constraints={"subcategory": "Ethnic Wear", "tags": ["ethnic"]},
            user_query="below 8000",
        )

        self.assertEqual(filters["product_query"], "ethnic wear")
        self.assertEqual(filters["subcategory"], "Ethnic Wear")

    def test_budget_reply_is_classified_as_recommendation_follow_up(self):
        state = {
            "latest_user_message": "below 4000",
            "session_id": "session-123",
        }

        with patch("sales_graph.nodes.intent_detector.get_recent_chat_turns", return_value=[]), patch(
            "sales_graph.nodes.intent_detector.get_recommendation_state",
            return_value={
                "product_query": "beauty products",
                "category": "beauty",
                "price_min": None,
                "price_max": None,
                "occasion": None,
                "subcategory": None,
                "tags": [],
            },
        ), patch("sales_graph.nodes.intent_detector.os.getenv", return_value=""):
            result = intent_detector_node(state)

        self.assertEqual(result["current_intent"], "refine_recommendations")
        self.assertEqual(result["conversation_act"], "follow_up_request")
        self.assertEqual(result["intent_entities"]["product_query"], "beauty products")

    def test_occasion_reply_is_classified_as_recommendation_follow_up(self):
        state = {
            "latest_user_message": "wedding",
            "session_id": "session-456",
        }

        with patch("sales_graph.nodes.intent_detector.get_recent_chat_turns", return_value=[]), patch(
            "sales_graph.nodes.intent_detector.get_recommendation_state",
            return_value={
                "product_query": "ethnic wear",
                "category": None,
                "price_min": None,
                "price_max": 8000,
                "occasion": None,
                "subcategory": "Ethnic Wear",
                "tags": ["ethnic"],
            },
        ), patch("sales_graph.nodes.intent_detector.os.getenv", return_value=""):
            result = intent_detector_node(state)

        self.assertEqual(result["current_intent"], "refine_recommendations")
        self.assertEqual(result["conversation_act"], "follow_up_request")
        self.assertEqual(result["intent_entities"]["subcategory"], "Ethnic Wear")


if __name__ == "__main__":
    unittest.main()
