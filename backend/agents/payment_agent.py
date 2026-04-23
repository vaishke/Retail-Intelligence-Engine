from datetime import datetime
import uuid

from bson import ObjectId
from bson.errors import InvalidId

from db.database import orders_collection


class PaymentAgent:
    SUPPORTED_METHODS = {"UPI", "CARD", "COD", "NETBANKING", "WALLET"}

    @staticmethod
    def process_payment(order_id: str, payment_method: str, details: dict = None):
        """
        Processes a mock payment for an order.
        Updates the order's payment sub-document with the simulated outcome.
        """
        details = details or {}
        normalized_order_id = PaymentAgent._normalize_order_id(order_id)
        normalized_method = PaymentAgent._normalize_payment_method(payment_method)

        if normalized_order_id is None:
            return {
                "success": False,
                "order_id": str(order_id),
                "message": "Invalid order id"
            }

        if not normalized_method:
            return {
                "success": False,
                "order_id": str(order_id),
                "message": "Unsupported payment method"
            }

        # Fetch the order
        order = orders_collection.find_one({"_id": normalized_order_id})

        if not order:
            return {
                "success": False,
                "order_id": str(order_id),
                "message": "Order not found"
            }

        # Check if already paid
        current_status = str(order.get("payment", {}).get("status", "")).lower()
        if current_status in {"paid", "success", "captured"}:
            return {
                "success": True,
                "order_id": str(order["_id"]),
                "transaction_id": order.get("payment", {}).get("transaction_id"),
                "amount": order.get("final_price", 0),
                "payment_method": order.get("payment", {}).get("method") or normalized_method,
                "gateway": order.get("payment", {}).get("gateway", "mock"),
                "message": "Order already paid"
            }

        amount = order.get("final_price", 0)
        success, gateway_message = PaymentAgent._simulate_mock_gateway(
            payment_method=normalized_method,
            amount=amount,
            details=details
        )
        transaction_id = PaymentAgent._build_transaction_id(normalized_method) if success else None
        payment_status = "paid" if success else "failed"

        # Update the order's payment sub-document
        orders_collection.update_one(
            {"_id": normalized_order_id},
            {"$set": {
                "payment.status": payment_status,
                "payment.method": normalized_method,
                "payment.transaction_id": transaction_id,
                "payment.details": details or {},
                "payment.gateway": "mock",
                "payment.updated_at": datetime.utcnow()
            }}
        )

        return {
            "success": success,
            "order_id": str(order["_id"]),
            "transaction_id": transaction_id,
            "amount": amount,
            "payment_method": normalized_method,
            "gateway": "mock",
            "message": gateway_message
        }

    @staticmethod
    def _normalize_order_id(order_id):
        if isinstance(order_id, ObjectId):
            return order_id

        try:
            return ObjectId(str(order_id))
        except (InvalidId, TypeError):
            return None

    @staticmethod
    def _normalize_payment_method(payment_method: str | None) -> str | None:
        if not payment_method:
            return None

        aliases = {
            "upi": "UPI",
            "card": "CARD",
            "credit card": "CARD",
            "debit card": "CARD",
            "cod": "COD",
            "cash on delivery": "COD",
            "netbanking": "NETBANKING",
            "net banking": "NETBANKING",
            "wallet": "WALLET",
        }

        normalized = aliases.get(str(payment_method).strip().lower(), str(payment_method).strip().upper())
        if normalized not in PaymentAgent.SUPPORTED_METHODS:
            return None
        return normalized

    @staticmethod
    def _simulate_mock_gateway(payment_method: str, amount: float, details: dict) -> tuple[bool, str]:
        forced_outcome = str(details.get("mock_result", "")).strip().lower()
        if forced_outcome in {"fail", "failed", "declined"}:
            return False, f"Mock payment declined for {payment_method}."

        if forced_outcome in {"success", "paid"}:
            return True, f"Mock payment successful via {payment_method}."

        if amount <= 0:
            return False, "Invalid payment amount."

        return True, f"Mock payment successful via {payment_method}."

    @staticmethod
    def _build_transaction_id(payment_method: str) -> str:
        return f"MOCK-{payment_method}-{uuid.uuid4().hex[:12].upper()}"
