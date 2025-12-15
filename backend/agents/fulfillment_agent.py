from backend.db.database import orders_collection, products_collection

class FulfillmentAgent:

    def process_order(self, order, user_location=None):
        fulfilled = []
        unfulfilled = []
        total = 0

        for item in order["products"]:
            product = products_collection.find_one({"sku": item["sku"]})

            if product and product["stock"] >= item["quantity"]:
                fulfilled.append(item)
                total += item["quantity"] * item["price"]

                products_collection.update_one(
                    {"sku": item["sku"]},
                    {"$inc": {"stock": -item["quantity"]}}
                )
            else:
                unfulfilled.append(item)

        status = "fulfilled" if not unfulfilled else "partial"

        orders_collection.insert_one({
            "order_id": order["order_id"],
            "user_id": order["user_id"],
            "fulfilled_products": fulfilled,
            "unfulfilled_products": unfulfilled,
            "total_amount": total,
            "status": status
        })

        return {
            "order_id": order["order_id"],
            "status": status,
            "fulfilled_products": fulfilled,
            "unfulfilled_products": unfulfilled
        }
