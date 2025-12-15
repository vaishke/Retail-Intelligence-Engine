from backend.agents.payment_agent.payment_agent import PaymentAgent

agent = PaymentAgent()

payment_request = {
    "order_id": "ORD001",
    "user_id": "USER01",
    "amount": 5000,
    "payment_method": "card",
    "details": {
        "card_number": "4111111111111111",
        "expiry": "12/26",
        "cvv": "123"
    }
}

response = agent.process_payment(payment_request)
print(response)
