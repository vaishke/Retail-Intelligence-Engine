import importlib
import sys
import types
import unittest
from unittest.mock import MagicMock

from bson import ObjectId


class PaymentAgentIdempotencyTests(unittest.TestCase):
    def test_already_paid_order_returns_successful_idempotent_response(self):
        fake_orders_collection = MagicMock()
        order_id = ObjectId()
        fake_orders_collection.find_one.return_value = {
            "_id": order_id,
            "final_price": 2499,
            "payment": {
                "status": "paid",
                "method": "COD",
                "transaction_id": "MOCK-COD-ABC123",
                "gateway": "mock",
            },
        }

        fake_db_module = types.ModuleType("db.database")
        fake_db_module.orders_collection = fake_orders_collection

        previous_db_module = sys.modules.get("db.database")
        previous_payment_module = sys.modules.get("agents.payment_agent")

        sys.modules["db.database"] = fake_db_module
        sys.modules.pop("agents.payment_agent", None)

        try:
            payment_module = importlib.import_module("agents.payment_agent")
            result = payment_module.PaymentAgent.process_payment(order_id, "cash on delivery")
        finally:
            if previous_db_module is not None:
                sys.modules["db.database"] = previous_db_module
            else:
                sys.modules.pop("db.database", None)

            if previous_payment_module is not None:
                sys.modules["agents.payment_agent"] = previous_payment_module
            else:
                sys.modules.pop("agents.payment_agent", None)

        self.assertTrue(result["success"])
        self.assertEqual(result["order_id"], str(order_id))
        self.assertEqual(result["payment_method"], "COD")
        self.assertEqual(result["transaction_id"], "MOCK-COD-ABC123")
        fake_orders_collection.update_one.assert_not_called()


if __name__ == "__main__":
    unittest.main()
