import importlib
import sys
import types
import unittest
from unittest.mock import MagicMock

from bson import ObjectId


class PaymentInventorySyncTests(unittest.TestCase):
    def _load_modules(self, order_doc, deduction_result=None):
        fake_orders_collection = MagicMock()
        fake_orders_collection.find_one.return_value = order_doc

        fake_inventory_agent_cls = MagicMock()
        fake_inventory_agent_cls.deduct_order_stock.return_value = deduction_result or {
            "success": True,
            "allocations": [
                {
                    "product_id": str(order_doc["items"][0]["product_id"]),
                    "qty": order_doc["items"][0]["qty"],
                    "store_id": "store_1",
                }
            ],
        }

        fake_db_module = types.ModuleType("db.database")
        fake_db_module.orders_collection = fake_orders_collection

        fake_inventory_module = types.ModuleType("agents.inventory_agent")
        fake_inventory_module.InventoryAgent = fake_inventory_agent_cls

        previous_db_module = sys.modules.get("db.database")
        previous_inventory_module = sys.modules.get("agents.inventory_agent")
        previous_payment_module = sys.modules.get("agents.payment_agent")
        previous_fulfillment_module = sys.modules.get("agents.fulfillment_agent")

        sys.modules["db.database"] = fake_db_module
        sys.modules["agents.inventory_agent"] = fake_inventory_module
        sys.modules.pop("agents.payment_agent", None)
        sys.modules.pop("agents.fulfillment_agent", None)

        try:
            payment_module = importlib.import_module("agents.payment_agent")
            fulfillment_module = importlib.import_module("agents.fulfillment_agent")
            return (
                payment_module,
                fulfillment_module,
                fake_orders_collection,
                fake_inventory_agent_cls,
            )
        finally:
            if previous_db_module is not None:
                sys.modules["db.database"] = previous_db_module
            else:
                sys.modules.pop("db.database", None)

            if previous_inventory_module is not None:
                sys.modules["agents.inventory_agent"] = previous_inventory_module
            else:
                sys.modules.pop("agents.inventory_agent", None)

            if previous_payment_module is not None:
                sys.modules["agents.payment_agent"] = previous_payment_module
            else:
                sys.modules.pop("agents.payment_agent", None)

            if previous_fulfillment_module is not None:
                sys.modules["agents.fulfillment_agent"] = previous_fulfillment_module
            else:
                sys.modules.pop("agents.fulfillment_agent", None)

    def test_successful_payment_deducts_inventory_and_marks_order(self):
        order_id = ObjectId()
        product_id = ObjectId()
        order_doc = {
            "_id": order_id,
            "final_price": 2499,
            "items": [{"product_id": product_id, "qty": 2, "price": 1249.5}],
            "payment": {"status": "pending"},
            "fulfillment": {},
        }

        payment_module, _, fake_orders_collection, fake_inventory_agent = self._load_modules(order_doc)

        result = payment_module.PaymentAgent.process_payment(order_id, "card", {"mock_result": "success"})

        self.assertTrue(result["success"])
        fake_inventory_agent.deduct_order_stock.assert_called_once()
        self.assertGreaterEqual(fake_orders_collection.update_one.call_count, 2)

    def test_fulfillment_skips_second_inventory_deduction_when_order_already_marked(self):
        order_id = ObjectId()
        product_id = ObjectId()
        order_doc = {
            "_id": order_id,
            "items": [{"product_id": product_id, "qty": 1, "price": 999}],
            "inventory": {
                "deducted": True,
                "allocations": [{"product_id": str(product_id), "qty": 1, "store_id": "store_1"}],
            },
        }

        _, fulfillment_module, fake_orders_collection, fake_inventory_agent = self._load_modules(order_doc)

        result = fulfillment_module.FulfillmentAgent.process_order(
            {
                "order_id": str(order_id),
                "user_id": ObjectId(),
                "items": [{"product_id": product_id, "qty": 1, "price": 999}],
                "fulfillment_type": "SHIP_TO_HOME",
            }
        )

        self.assertTrue(result["success"])
        fake_inventory_agent.deduct_order_stock.assert_not_called()
        fake_orders_collection.update_one.assert_called()


if __name__ == "__main__":
    unittest.main()
