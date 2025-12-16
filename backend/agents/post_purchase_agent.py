from db.database import inventory_collection, orders_collection, shipments_collection, invoices_collection, notifications_collection
import uuid
from datetime import datetime

class PostPurchaseAgent:
    '''
    {
  "order_id": "ORD123",
  "user_id": "USER01",
  "transaction_id": "TXN789",
  "cart_items": [
    { "sku": "SHOE001", "quantity": 2 },
    { "sku": "TSHIRT001", "quantity": 1 }
  ],
  "final_amount": 4500,
  "delivery_address": {
    "city": "Hyderabad",
    "pincode": "500001"
  }
}

    '''
    @staticmethod
    def confirm_order(order_id, transaction_id):
        order = orders_collection.find_one({"order_id": order_id})

        if not order:
            raise ValueError("Order not found")
        
        if order.get("status") == "confirmed":
            return {
                "order_id": order_id,
                "status": "already_confirmed",
                "message": "Order was already confirmed"
            }
        
        orders_collection.update_one(
            {"order_id": order_id},
            {
                "$set": {
                    "status": "confirmed",
                    "transaction_id": transaction_id,
                    "confirmed_at": datetime.utcnow()
                }
            }
        )

        return {
            "order_id": order_id,
            "status": "confirmed",
            "message": "Order confirmed successfully"
        }


    @staticmethod
    def reduce_inventory(delivery_city, cart_items):
        for item in cart_items:
            sku = item["sku"]
            quantity_needed = item["quantity"]

            record = inventory_collection.find_one({"sku": sku})

            if not record:
                raise Exception(f"Inventory record not found for SKU {sku}")

            store_stock = record.get("storeStock", {})
            online_stock = record.get("availableOnline", 0)

            city_stock = store_stock.get(delivery_city, 0)
            # Case 1: Enough stock in delivery city store
            if city_stock >= quantity_needed:
                inventory_collection.update_one(
                    {"sku": sku},
                    {"$inc": {f"storeStock.{delivery_city}": -quantity_needed}}
                )

            # Case 2: Partial store + online stock
            elif city_stock > 0 and (city_stock + online_stock) >= quantity_needed:
                remaining = quantity_needed - city_stock

                inventory_collection.update_one(
                    {"sku": sku},
                    {
                        "$set": {f"storeStock.{delivery_city}": 0},
                        "$inc": {"availableOnline": -remaining}
                    }
                )
            # Case 3: Only online stock
            elif online_stock >= quantity_needed:
                inventory_collection.update_one(
                    {"sku": sku},
                    {"$inc": {"availableOnline": -quantity_needed}}
                )

            # Case 4: Insufficient stock
            else:
                raise Exception(
                    f"Insufficient stock for SKU {sku} "
                    f"(requested {quantity_needed}, available {city_stock + online_stock})"
                )

        return {
            "success": True,
            "message": "Inventory successfully updated"
        }

    @staticmethod
    def create_shipment(order_id, delivery_address):
        shipment_id = f"SHP-{uuid.uuid4().hex[:8]}"

        shipment = {
            "shipment_id": shipment_id,
            "order_id": order_id,
            "delivery_address": delivery_address,
            "status": "processing",
            "created_at": datetime.utcnow()
        }

        shipments_collection.insert_one(shipment)

        return {
            "shipment_id": shipment_id,
            "status": "processing"
        }

    
    @staticmethod
    def generate_invoice(order_id, cart_items, final_amount):
        invoice_id = f"INV-{uuid.uuid4().hex[:8]}"

        invoice = {
            "invoice_id": invoice_id,
            "order_id": order_id,
            "items": cart_items,
            "final_amount": final_amount,
            "issued_at": datetime.utcnow()
        }

        invoices_collection.insert_one(invoice)

        return {
            "invoice_id": invoice_id,
            "amount": final_amount
        }
    
    @staticmethod
    def send_notification(user_id, order_id):
        notification = {
            "user_id": user_id,
            "type": "ORDER_CONFIRMED",
            "message": f"Your order {order_id} has been successfully placed.",
            "read": False,
            "created_at": datetime.utcnow()
        }

        notifications_collection.insert_one(notification)

        return {
            "success": True,
            "message": "Notification sent"
        }

    @staticmethod
    def handle_post_purchase(input_json):
    

        if not input_json:
            return {
                "success": False,
                "message": "Input payload is missing"
            }

        required_fields = [
            "order_id",
            "transaction_id",
            "user_id",
            "cart_items",
            "final_amount",
            "delivery_address"
        ]

        for field in required_fields:
            if field not in input_json or input_json[field] is None:
                return {
                    "success": False,
                    "message": f"Missing required field: {field}"
                }

        delivery_address = input_json["delivery_address"]

        if not isinstance(delivery_address, dict):
            return {
                "success": False,
                "message": "delivery_address must be an object"
            }

        if "city" not in delivery_address or not delivery_address["city"]:
            return {
                "success": False,
                "message": "delivery_address.city is required"
            }

        cart_items = input_json["cart_items"]

        if not isinstance(cart_items, list) or len(cart_items) == 0:
            return {
                "success": False,
                "message": "cart_items must be a non-empty list"
            }

        for item in cart_items:
            if not all(k in item for k in ("sku", "quantity")):
                return {
                    "success": False,
                    "message": "Each cart item must have sku, price, and quantity"
                }

            if item["quantity"] <= 0:
                return {
                    "success": False,
                    "message": f"Invalid price or quantity for SKU {item.get('sku')}"
                }

        order_id = input_json.get("order_id")
        transaction_id = input_json.get("transaction_id")
        user_id = input_json.get("user_id")
        cart_items = input_json.get("cart_items")
        final_amount = input_json.get("final_amount")
        delivery_address = input_json.get("delivery_address")

        try:
            PostPurchaseAgent.confirm_order(order_id, transaction_id)
            PostPurchaseAgent.reduce_inventory(delivery_address["city"], cart_items)
            shipment_json = PostPurchaseAgent.create_shipment(order_id, delivery_address)
            invoice_json = PostPurchaseAgent.generate_invoice(order_id, cart_items, final_amount)
            PostPurchaseAgent.send_notification(user_id, order_id)

            return {
                    "success": True,
                    "order_id": order_id,
                    "shipment_id": shipment_json.get("shipment_id"),
                    "invoice_id": invoice_json.get("invoice_id"),
                    "message": "Order confirmed and post-purchase steps completed"
                }
        except Exception as e:
            return {
                "success": False,
                "message": "Post-purchase processing failed",
                "error": str(e)
            }
            

