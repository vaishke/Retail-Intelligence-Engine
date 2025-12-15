from agents.payment_agent.payment_agent import PaymentAgent

agent = PaymentAgent()

class PaymentService:

    @staticmethod
    def process_payment_service(payment_request: dict):
        return agent.process_payment(payment_request)