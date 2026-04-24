import unittest
from unittest.mock import MagicMock, patch

from bson import ObjectId

from sales_graph.nodes.inventory import inventory_agent_node
from sales_graph.nodes.response_generator import response_generator_node
from services.cart_service import CartService
from services.order_service import OrderService


class StockGuardTests(unittest.TestCase):
    @patch("services.cart_service.products_collection")
    @patch("services.cart_service.users_collection")
    @patch("services.cart_service.InventoryAgent.check_stock")
    def test_add_to_cart_rejects_out_of_stock_item(self, mock_check_stock, mock_users, mock_products):
        mock_users.find_one.return_value = {"_id": ObjectId(), "cart": {"items": []}}
        mock_products.find_one.return_value = {"_id": ObjectId(), "name": "Laptop Sleeve", "price": 999}
        mock_check_stock.return_value = {
            "success": True,
            "isAvailable": False,
            "availableQuantity": 0,
        }

        result = CartService.add_or_update_item(
            user_id=str(ObjectId()),
            product_id=str(ObjectId()),
            quantity=1,
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["code"], "OUT_OF_STOCK")
        self.assertIn("out of stock", result["message"].lower())
        mock_users.update_one.assert_not_called()

    @patch("services.order_service.OfferLoyaltyAgent.process_checkout")
    @patch("services.order_service.InventoryAgent.check_stock")
    def test_place_order_stops_before_payment_when_inventory_is_unavailable(
        self,
        mock_check_stock,
        mock_process_checkout,
    ):
        mock_check_stock.return_value = {
            "success": True,
            "productName": "Sneakers",
            "availableQuantity": 0,
            "isAvailable": False,
        }

        result = OrderService.place_order(
            {
                "user_id": str(ObjectId()),
                "items": [{"product_id": str(ObjectId()), "qty": 1, "price": 1999}],
                "payment_method": "COD",
            }
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["stage"], "inventory")
        self.assertIn("out of stock", result["message"].lower())
        mock_process_checkout.assert_not_called()

    @patch("sales_graph.nodes.inventory.InventoryAgent.check_stock")
    def test_inventory_node_marks_cart_unavailable_when_requested_qty_exceeds_stock(self, mock_check_stock):
        mock_check_stock.return_value = {
            "success": True,
            "product_id": "p1",
            "productName": "Running Shoes",
            "totalStock": 1,
            "storeStock": 1,
            "requestedQuantity": 2,
            "availableQuantity": 1,
            "isAvailable": False,
        }

        result = inventory_agent_node(
            {
                "cart_items": [{"product_id": "p1", "qty": 2, "price": 2499}],
                "location": {},
                "agent_call_history": [],
            }
        )

        self.assertFalse(result["inventory_verified"])
        self.assertEqual(result["last_error"]["code"], "ITEM_UNAVAILABLE")
        self.assertEqual(result["last_error"]["unavailable_items"][0]["available_quantity"], 1)

    def test_response_generator_surfaces_out_of_stock_cart_message(self):
        response = response_generator_node(
            {
                "confirmation_context": "error_response",
                "last_error": {
                    "code": "ITEM_UNAVAILABLE",
                    "message": "1 item(s) out of stock",
                    "unavailable_items": [
                        {
                            "product_name": "Running Shoes",
                            "requested_quantity": 2,
                            "available_quantity": 0,
                        }
                    ],
                },
                "session_id": None,
            }
        )["response"]

        self.assertIn("out of stock", response["message"].lower())
        self.assertIn("cart", response["message"].lower())


if __name__ == "__main__":
    unittest.main()
