from agents.payment_agent import PaymentAgent

agent = PaymentAgent()

class PaymentService:

    @staticmethod
    def process_payment_service(data: dict):
        """
        data must include:
        - order_id
        - payment_method
        - details (optional)
        """
        return agent.process_payment(
            order_id=data["order_id"],
            payment_method=data["payment_method"],
            details=data.get("details")
        )
