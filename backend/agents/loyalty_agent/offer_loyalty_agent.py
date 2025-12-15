from db.database import users_collection, offers_collection, orders_collection
from datetime import datetime


class OfferLoyaltyAgent:
    """
    Handles:
    - Coupon application
    - Loyalty points redemption
    - Loyalty points earning
    - Tier upgrades
    - Order summary persistence
    """

    # 🔹 Loyalty configuration
    POINTS_PER_100 = 1       # Earn 1 point per ₹100 spent
    POINT_VALUE = 1          # 1 point = ₹1

    TIERS = {
        "Silver": 0,
        "Gold": 5000,
        "Platinum": 15000
    }

    def __init__(self):
        self.users = users_collection
        self.offers = offers_collection
        self.orders = orders_collection

    # -------------------------------------------------
    # USER / LOYALTY HELPERS
    # -------------------------------------------------

    def get_user(self, user_id):
        """
        Fetch user or auto-create if not exists
        """
        user = self.users.find_one({"user_id": user_id})

        if not user:
            self.users.insert_one({
                "user_id": user_id,
                "points": 0,
                "tier": "Silver",
                "total_spent": 0,
                "created_at": datetime.utcnow()
            })
            user = self.users.find_one({"user_id": user_id})

        return user

    def calculate_tier(self, total_spent):
        """
        Determine loyalty tier
        """
        if total_spent >= self.TIERS["Platinum"]:
            return "Platinum"
        elif total_spent >= self.TIERS["Gold"]:
            return "Gold"
        return "Silver"

    def earn_points(self, amount):
        """
        Earn points based on spend
        """
        return (amount // 100) * self.POINTS_PER_100

    # -------------------------------------------------
    # OFFER HELPERS
    # -------------------------------------------------

    def apply_coupon(self, coupon_code, cart_total):
        """
        Validate and apply coupon
        """
        offer = self.offers.find_one({
            "code": coupon_code,
            "active": True
        })

        if not offer:
            return 0, "Invalid or expired coupon"

        if cart_total < offer.get("min_cart_value", 0):
            return 0, "Cart value too low for this coupon"

        if offer["type"] == "flat":
            discount = offer["value"]
        elif offer["type"] == "percentage":
            discount = (offer["value"] / 100) * cart_total
        else:
            discount = 0

        return discount, "Coupon applied successfully"

    # -------------------------------------------------
    # MAIN CHECKOUT FUNCTION
    # -------------------------------------------------

    def process_checkout(self, user_id, cart_items, coupon_code=None, use_points=0):
        """
        cart_items format:
        [
            {"sku": "S123", "price": 1000, "quantity": 2},
            {"sku": "S555", "price": 500, "quantity": 1}
        ]
        """

        # 1️⃣ Calculate cart total
        cart_total = sum(
            item["price"] * item["quantity"] for item in cart_items
        )

        # 2️⃣ Fetch user
        user = self.get_user(user_id)
        old_points = user["points"]
        old_total_spent = user["total_spent"]

        # 3️⃣ Apply coupon
        coupon_discount = 0
        coupon_message = None
        if coupon_code:
            coupon_discount, coupon_message = self.apply_coupon(
                coupon_code, cart_total
            )

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
                {"user_id": user_id},
                {"$inc": {"points": -use_points}}
            )

        # 5️⃣ Final payable amount
        final_amount = max(
            cart_total - coupon_discount - points_discount, 0
        )

        # 6️⃣ Earn new loyalty points
        earned_points = self.earn_points(final_amount)
        self.users.update_one(
            {"user_id": user_id},
            {"$inc": {"points": earned_points}}
        )

        # 7️⃣ Update total spent & tier
        new_total_spent = old_total_spent + final_amount
        new_tier = self.calculate_tier(new_total_spent)

        self.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "total_spent": new_total_spent,
                    "tier": new_tier
                }
            }
        )

        # 8️⃣ Save order summary
        self.orders.insert_one({
            "user_id": user_id,
            "cart_items": cart_items,
            "cart_total": cart_total,
            "coupon_code": coupon_code,
            "coupon_discount": coupon_discount,
            "points_used": use_points,
            "points_earned": earned_points,
            "final_amount": final_amount,
            "tier_after_purchase": new_tier,
            "created_at": datetime.utcnow()
        })

        # 9️⃣ Return response
        return {
            "success": True,
            "cart_total": cart_total,
            "coupon_discount": coupon_discount,
            "coupon_message": coupon_message,
            "loyalty_points_used": use_points,
            "loyalty_points_earned": earned_points,
            "final_amount": final_amount,
            "new_tier": new_tier
        }

    # -------------------------------------------------
    # QUERY FUNCTIONS
    # -------------------------------------------------

    def get_user_loyalty_status(self, user_id):
        user = self.get_user(user_id)
        return {
            "user_id": user_id,
            "points": user["points"],
            "tier": user["tier"],
            "total_spent": user["total_spent"]
        }

    def view_available_offers(self):
        return list(
            self.offers.find({"active": True}, {"_id": 0})
        )
