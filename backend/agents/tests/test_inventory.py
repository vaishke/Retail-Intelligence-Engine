from pprint import pprint
from db.database import products_collection
from agents.inventory_agent import InventoryAgent


def get_sample_product_id():
    product = products_collection.find_one()
    if not product:
        raise Exception("No products found in DB")
    return product["_id"]


def main():
    product_id = get_sample_product_id()
    print(f"\nTesting Inventory for Product ID: {product_id}\n")

    print("=== CHECK TOTAL STOCK ===")
    result_total = InventoryAgent.handle_request({
        "action": "check_stock",
        "product_id": product_id
    })
    pprint(result_total)

    print("\n=== CHECK STOCK FOR store_1 ===")
    result_store = InventoryAgent.handle_request({
        "action": "check_stock",
        "product_id": product_id,
        "userLocation": "store_1"
    })
    pprint(result_store)
    print("\n=== CHECK STOCK FOR store_2 ===")
    result_store = InventoryAgent.handle_request({
        "action": "check_stock",
        "product_id": product_id,
        "userLocation": "store_2"
    })
    pprint(result_store)

    print("\n=== STORE-WISE STOCK BREAKDOWN ===")
    result_breakdown = InventoryAgent.handle_request({
        "action": "get_store_stock",
        "product_id": product_id
    })
    pprint(result_breakdown)


if __name__ == "__main__":
    main()