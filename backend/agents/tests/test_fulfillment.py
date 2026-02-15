# test_fulfillment.py

from agents.fulfillment_agent import FulfillmentAgent
from db.database import inventory_collection
from pprint import pprint

# Product: Floral Summer Dress
PRODUCT_ID = "6990a3045837cd6bdc137a44"
STORE_ID = "store_1"

print("\n=== BEFORE FULFILLMENT ===")
before = list(inventory_collection.find({
    "product_id": PRODUCT_ID,
    "store_id": STORE_ID
}))
pprint(before)

# Order matching your order schema style
order = {
    "order_id": "ORD_TEST_001",
    "user_id": "USER_001",
    "fulfillment_type": "CLICK_AND_COLLECT",
    "store_location": STORE_ID,
    "items": [
        {
            "product_id": PRODUCT_ID,
            "qty": 3,
            "price": 1499
        }
    ]
}

print("\n=== RUNNING FULFILLMENT ===")
result = FulfillmentAgent.process_order(order)
pprint(result)

print("\n=== AFTER FULFILLMENT ===")
after = list(inventory_collection.find({
    "product_id": PRODUCT_ID,
    "store_id": STORE_ID
}))
pprint(after)