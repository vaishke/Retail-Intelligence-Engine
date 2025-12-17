from agents.payment_agent import PaymentAgent

agent = PaymentAgent()


class PaymentService:

    @staticmethod
    def process_payment_service(data: dict):
        order_id = data.get("order_id")
        payment_method = data.get("payment_method")
        details = data.get("details")

        if not order_id or not payment_method:
            return {
                "success": False,
                "order_id": order_id or "",
                "message": "order_id and payment_method are required"
            }

        return agent.process_payment(order_id, payment_method, details)
