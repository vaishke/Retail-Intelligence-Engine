import unittest
from unittest.mock import patch

from sales_graph.nodes.intent_detector import classify_intent_rules, extract_entities_rules, intent_detector_node
from sales_graph.nodes.response_generator import response_generator_node
from sales_graph.nodes.sales_planner import planner_policy


class CheckoutFlowStateTests(unittest.TestCase):
    def test_checkout_confirmation_prompts_for_payment_and_sets_stage(self):
        state = {
            "cart_items": [{"product_id": "p1", "name": "Earbuds", "qty": 1, "price": 2499}],
            "silent_chains_this_turn": 0,
        }

        result = planner_policy("checkout_confirmation", state)

        self.assertEqual(result["next_action"], "respond")
        self.assertTrue(result["await_confirmation"])
        self.assertEqual(result["confirmation_context"], "choose_payment_method")
        self.assertEqual(result["checkout_stage"], "awaiting_payment_method")

    def test_payment_method_selection_continues_checkout_using_stage(self):
        state = {
            "cart_items": [{"product_id": "p1", "name": "Earbuds", "qty": 1, "price": 2499}],
            "checkout_stage": "awaiting_payment_method",
            "intent_entities": {"payment_method": "COD"},
            "silent_chains_this_turn": 0,
        }

        result = planner_policy("payment_method_selection", state)

        self.assertEqual(result["next_action"], "loyalty_offers_agent")
        self.assertEqual(result["payment_method"], "COD")
        self.assertEqual(result["checkout_stage"], "summary_ready")

    def test_payment_method_selection_without_checkout_returns_recovery_message(self):
        state = {
            "cart_items": [],
            "checkout_stage": None,
            "confirmation_context": "checkout_context_lost",
        }

        response = response_generator_node(state)["response"]

        self.assertIn("checkout context", response["message"].lower())

    def test_choose_payment_method_uses_checkout_context_amount(self):
        state = {
            "confirmation_context": "choose_payment_method",
            "checkout_context": {"final_amount": 2499},
        }

        response = response_generator_node(state)["response"]

        self.assertEqual(response["data"]["final_amount"], 2499)

    def test_combined_checkout_and_payment_message_is_checkout_confirmation(self):
        intent = classify_intent_rules("proceed to checkout cash on delivery")

        self.assertEqual(intent, "checkout_confirmation")

    def test_track_my_order_is_classified_as_order_tracking(self):
        intent = classify_intent_rules("track my order")

        self.assertEqual(intent, "order_tracking")

    def test_show_recent_orders_is_classified_as_order_tracking(self):
        intent = classify_intent_rules("show my recent orders")

        self.assertEqual(intent, "order_tracking")

    def test_order_tracking_response_uses_post_purchase_state(self):
        state = {
            "current_intent": "order_tracking",
            "last_worker": "post_purchase_agent",
            "order_status": {
                "order_id": "order-123",
                "status": "confirmed",
                "tracking_status": "processing",
                "tracking_number": "TRK-123",
                "shipment_id": "ship-123",
                "invoice_id": "inv-123",
                "final_amount": 1899,
                "items": [{"name": "Linen Blend Kurta Set", "qty": 1, "price": 1899}],
                "tracking_lookup": True,
            },
        }

        response = response_generator_node(state)["response"]

        self.assertIn("latest update", response["message"].lower())
        self.assertEqual(response["data"]["tracking_number"], "TRK-123")

    def test_order_id_is_extracted_for_tracking_queries(self):
        entities = extract_entities_rules("track order 507f1f77bcf86cd799439011")

        self.assertEqual(entities["order_id"], "507f1f77bcf86cd799439011")

    def test_recent_orders_flag_is_extracted(self):
        entities = extract_entities_rules("show recent orders")

        self.assertTrue(entities["list_orders"])

    def test_order_tracking_responds_after_post_purchase_worker_runs(self):
        state = {
            "current_intent": "order_tracking",
            "last_worker": "post_purchase_agent",
            "silent_chains_this_turn": 0,
        }

        result = planner_policy("order_tracking", state)

        self.assertEqual(result["next_action"], "respond")
        self.assertFalse(result["await_confirmation"])

    def test_recent_orders_response_uses_post_purchase_state(self):
        state = {
            "current_intent": "order_tracking",
            "last_worker": "post_purchase_agent",
            "order_status": {
                "tracking_lookup": True,
                "listing_orders": True,
                "recent_orders": [
                    {"order_id": "o1", "status": "confirmed", "final_amount": 1599}
                ],
            },
        }

        response = response_generator_node(state)["response"]

        self.assertIn("recent orders", response["message"].lower())
        self.assertEqual(len(response["data"]["recent_orders"]), 1)

    def test_intent_detector_uses_llm_result_when_available(self):
        state = {
            "latest_user_message": "can you check my latest order",
            "session_id": "session-123",
        }

        with patch("sales_graph.nodes.intent_detector.infer_intent_with_groq") as mock_infer, patch(
            "sales_graph.nodes.intent_detector.get_recent_chat_turns"
        ) as mock_recent_turns, patch("sales_graph.nodes.intent_detector.os.getenv", return_value="test-key"):
            mock_recent_turns.return_value = [{"role": "assistant", "message": "Your order was placed."}]
            mock_infer.return_value = {
                "intent": "order_tracking",
                "entities": {"list_orders": True},
                "conversation_act": "follow_up_request",
                "confidence": 0.91,
            }

            result = intent_detector_node(state)

        self.assertEqual(result["current_intent"], "order_tracking")
        self.assertTrue(result["intent_entities"]["list_orders"])
        self.assertEqual(result["conversation_act"], "follow_up_request")
        self.assertAlmostEqual(result["intent_confidence"], 0.91)

    def test_short_payment_follow_up_uses_checkout_context(self):
        state = {
            "latest_user_message": "yes please",
            "checkout_stage": "summary_ready",
            "last_worker": "loyalty_offers_agent",
            "session_id": "session-123",
        }

        with patch("sales_graph.nodes.intent_detector.get_recent_chat_turns", return_value=[]), patch(
            "sales_graph.nodes.intent_detector.os.getenv", return_value=""
        ):
            result = intent_detector_node(state)

        self.assertEqual(result["current_intent"], "checkout_confirmation")
        self.assertEqual(result["conversation_act"], "confirmation")


if __name__ == "__main__":
    unittest.main()
