from db.database import users_collection, offers_collection, orders_collection
from datetime import datetime


class OfferLoyaltyAgent:
    """
    Handles:
    - Coupon application
    - Loyalty points redemption
    - Loyalty points earning
    - Tier upgrades
    - Order persistence according to schema
    """

    POINTS_PER_100 = 1   # Earn 1 point per ₹100 spent
    POINT_VALUE = 1      # 1 point = ₹1
    TIERS = {
        "Silver": 0,
        "Gold": 5000,
        "Platinum": 15000
    }

    def __init__(self):
        self.users = users_collection
        self.offers = offers_collection
        self.orders = orders_collection

    # ------------------------
    # USER / LOYALTY HELPERS
    # ------------------------
    def get_user(self, user_id):
        user = self.users.find_one({"_id": user_id})
        if not user:
            # Create a new user with loyalty object if not exists
            self.users.insert_one({
                "_id": user_id,
                "loyalty": {
                    "tier": "Silver",
                    "points": 0
                },
                "past_purchases": [],
                "created_at": datetime.utcnow()
            })
            user = self.users.find_one({"_id": user_id})
        return user

    def calculate_tier(self, total_points):
        if total_points >= self.TIERS["Platinum"]:
            return "Platinum"
        elif total_points >= self.TIERS["Gold"]:
            return "Gold"
        return "Silver"

    def earn_points(self, amount):
        return (amount // 100) * self.POINTS_PER_100

    # ------------------------
    # OFFER HELPERS
    # ------------------------
    def apply_coupon(self, coupon_code, cart_total):
        offer = self.offers.find_one({
            "code": coupon_code,
            "is_active": True
        })

        if not offer:
            return 0, "Invalid or expired coupon"

        if cart_total < offer.get("min_purchase_amount", 0):
            return 0, "Cart value too low for this offer"

        discount_percent = offer.get("discount_percent", 0)
        discount = (discount_percent / 100) * cart_total
        return discount, "Coupon applied successfully"

    # ------------------------
    # MAIN CHECKOUT FUNCTION
    # ------------------------
    def process_checkout(self, user_id, cart_items, coupon_code=None, use_points=0):
        """
        cart_items: [{"product_id": ObjectId, "qty": Number, "price": Number}]
        """

        # 1️⃣ Calculate cart total
        cart_total = sum(item["price"] * item["qty"] for item in cart_items)

        # 2️⃣ Fetch user
        user = self.get_user(user_id)
        old_points = user.get("loyalty", {}).get("points", 0)

        # 3️⃣ Apply coupon
        coupon_discount = 0
        coupon_message = None
        if coupon_code:
            coupon_discount, coupon_message = self.apply_coupon(coupon_code, cart_total)

        # 4️⃣ Redeem loyalty points
        points_discount = 0
        if use_points > 0:
            if use_points > old_points:
                return {
                    "success": False,
                    "message": "Insufficient loyalty points"
                }
            points_discount = use_points * self.POINT_VALUE
            self.users.update_one(
                {"_id": user_id},
                {"$inc": {"loyalty.points": -use_points}}
            )

        # 5️⃣ Final amount
        final_amount = max(cart_total - coupon_discount - points_discount, 0)

        # 6️⃣ Earn points
        earned_points = self.earn_points(final_amount)
        self.users.update_one(
            {"_id": user_id},
            {"$inc": {"loyalty.points": earned_points}}
        )

        # 7️⃣ Update tier
        total_points_after = old_points - use_points + earned_points
        new_tier = self.calculate_tier(total_points_after)
        self.users.update_one(
            {"_id": user_id},
            {"$set": {"loyalty.tier": new_tier}}
        )

        # 8️⃣ Save order according to schema
        order_doc = {
            "user_id": user_id,
            "session_id": None,
            "items": [
                {"product_id": item["product_id"], "qty": item["qty"], "price": item["price"]}
                for item in cart_items
            ],
            "discounts_applied": [],
            "final_price": final_amount,
            "payment": {
                "status": "PENDING",
                "method": None,
                "transaction_id": None,
                "updated_at": datetime.utcnow()
            },
            "fulfillment": {
                "type": None,
                "status": "PENDING"
            },
            "status": "pending",
            "created_at": datetime.utcnow(),
            "confirmed_at": None
        }

        # Add coupon if applied
        if coupon_code and coupon_discount > 0:
            order_doc["discounts_applied"].append({
                "type": "percentage",
                "code": coupon_code,
                "amount": coupon_discount
            })

        self.orders.insert_one(order_doc)

        # 9️⃣ Return response
        return {
            "success": True,
            "cart_total": cart_total,
            "coupon_discount": coupon_discount,
            "coupon_message": coupon_message,
            "loyalty_points_used": use_points,
            "loyalty_points_earned": earned_points,
            "final_amount": final_amount,
            "new_tier": new_tier,
            "order_id": order_doc["_id"]
        }

    # ------------------------
    # QUERY FUNCTIONS
    # ------------------------
    def get_user_loyalty_status(self, user_id):
        user = self.get_user(user_id)
        loyalty = user.get("loyalty", {})
        return {
            "user_id": user_id,
            "points": loyalty.get("points", 0),
            "tier": loyalty.get("tier", "Silver")
        }

    def view_available_offers(self):
        return list(self.offers.find({"is_active": True}, {"_id": 0}))