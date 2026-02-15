from datetime import datetime
from db.database import products_collection, inventory_collection

def seed_inventory_from_products():
    products = list(products_collection.find())

    inventory_docs = []

    for product in products:
        product_id = str(product["_id"])  # store as string for consistency

        for store in product.get("available_stores", []):
            inventory_docs.append({
                "product_id": product_id,
                "store_id": store["store_id"],
                "quantity": store["stock"],
                "last_updated": datetime.utcnow()
            })

    if inventory_docs:
        inventory_collection.insert_many(inventory_docs)
        print(f"Inserted {len(inventory_docs)} inventory records.")
    else:
        print("No inventory data found to insert.")

if __name__ == "__main__":
    seed_inventory_from_products()