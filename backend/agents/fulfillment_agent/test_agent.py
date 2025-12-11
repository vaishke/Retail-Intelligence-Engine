from fulfillment_agent import FulfillmentAgent

agent = FulfillmentAgent()

orders = [
    {
        "order_id": "ORD001",
        "user_id": "USER01",
        "products": [
            {"sku": "SHOE123", "quantity": 2, "price": 2999},
            {"sku": "SHOE321", "quantity": 1, "price": 2799}
        ],
        "total_amount": 0,
        "status": "pending"
    }
]

results = agent.process_orders_batch(orders, userLocation="Hyderabad")
for r in results:
    print(r)
