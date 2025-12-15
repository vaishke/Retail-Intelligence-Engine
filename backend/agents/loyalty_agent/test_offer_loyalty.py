from backend.agents.loyalty_agent.offer_loyalty_agent import OfferLoyaltyAgent
from backend.db.env_test import users_collection, offers_collection, orders_collection

def print_test(test_name, condition):
    status = "✅ PASS" if condition else "❌ FAIL"
    print(f"{status} - {test_name}")

def run_all_tests():
    agent = OfferLoyaltyAgent()

    # -------------------------------------------------
    # CLEAN DATABASE
    # -------------------------------------------------
    users_collection.delete_many({})
    offers_collection.delete_many({})
    orders_collection.delete_many({})

    # -------------------------------------------------
    # INSERT TEST OFFERS
    # -------------------------------------------------
    offers_collection.insert_many([
        {
            "code": "NEW50",
            "type": "flat",
            "value": 50,
            "min_cart_value": 500,
            "active": True
        },
        {
            "code": "PERC10",
            "type": "percentage",
            "value": 10,
            "min_cart_value": 1000,
            "active": True
        },
        {
            "code": "EXPIRED",
            "type": "flat",
            "value": 100,
            "min_cart_value": 500,
            "active": False
        }
    ])

    cart = [
        {"sku": "S123", "price": 2000, "quantity": 1},
        {"sku": "S555", "price": 500, "quantity": 2}
    ]

    # -------------------------------------------------
    # TEST 1: AUTO CREATE USER
    # -------------------------------------------------
    user = agent.get_user("USER01")
    print_test("User auto-created", user["tier"] == "Silver" and user["points"] == 0)

    # -------------------------------------------------
    # TEST 2: APPLY VALID FLAT COUPON
    # -------------------------------------------------
    discount, _ = agent.apply_coupon("NEW50", 3000)
    print_test("Flat coupon applied", discount == 50)

    # -------------------------------------------------
    # TEST 3: APPLY VALID PERCENT COUPON
    # -------------------------------------------------
    discount, _ = agent.apply_coupon("PERC10", 2000)
    print_test("Percentage coupon applied", discount == 200)

    # -------------------------------------------------
    # TEST 4: INVALID COUPON
    # -------------------------------------------------
    discount, msg = agent.apply_coupon("FAKE", 2000)
    print_test("Invalid coupon rejected", discount == 0)

    # -------------------------------------------------
    # TEST 5: COUPON MIN CART FAILURE
    # -------------------------------------------------
    discount, msg = agent.apply_coupon("NEW50", 200)
    print_test("Min cart restriction enforced", discount == 0)

    # -------------------------------------------------
    # TEST 6: CHECKOUT WITH COUPON ONLY
    # -------------------------------------------------
    response = agent.process_checkout(
        user_id="USER01",
        cart_items=cart,
        coupon_code="NEW50",
        use_points=0
    )
    print_test("Checkout success", response["success"])
    print_test("Final amount correct", response["final_amount"] == 2950)

    # -------------------------------------------------
    # TEST 7: EARN LOYALTY POINTS
    # -------------------------------------------------
    user = users_collection.find_one({"user_id": "USER01"})
    print_test("Points earned correctly", user["points"] == 29)

    # -------------------------------------------------
    # TEST 8: REDEEM VALID POINTS
    # -------------------------------------------------
    response = agent.process_checkout(
        user_id="USER01",
        cart_items=cart,
        use_points=10
    )
    print_test("Points redeemed", response["loyalty_points_used"] == 10)

    # -------------------------------------------------
    # TEST 9: REDEEM MORE THAN AVAILABLE
    # -------------------------------------------------
    response = agent.process_checkout(
        user_id="USER01",
        cart_items=cart,
        use_points=999
    )
    print_test("Over redemption blocked", response["success"] is False)

    # -------------------------------------------------
    # TEST 10: FINAL AMOUNT NEVER NEGATIVE
    # -------------------------------------------------
    # response = agent.process_checkout(
    #     user_id="USER02",
    #     cart_items=[{"sku": "X", "price": 100, "quantity": 1}],
    #     coupon_code="NEW50",
    #     use_points=100
    # )
    # print_test("Final amount >= 0", response["final_amount"] >= 0)

    # -------------------------------------------------
    # TEST 11: TIER UPGRADE TO GOLD
    # -------------------------------------------------
    users_collection.update_one(
        {"user_id": "USER03"},
        {"$set": {"total_spent": 4900}}
    )
    response = agent.process_checkout(
        user_id="USER03",
        cart_items=[{"sku": "A", "price": 200, "quantity": 1}]
    )
    print_test("Tier upgraded to Gold", response["new_tier"] == "Gold")

    # -------------------------------------------------
    # TEST 12: TIER UPGRADE TO PLATINUM
    # -------------------------------------------------
    users_collection.update_one(
        {"user_id": "USER04"},
        {"$set": {"total_spent": 14800}}
    )
    response = agent.process_checkout(
        user_id="USER04",
        cart_items=[{"sku": "B", "price": 300, "quantity": 1}]
    )
    print_test("Tier upgraded to Platinum", response["new_tier"] == "Platinum")

    # -------------------------------------------------
    # TEST 13: ORDER SAVED
    # -------------------------------------------------
    order_count = orders_collection.count_documents({})
    print_test("Orders saved", order_count > 0)

    # -------------------------------------------------
    # TEST 14: VIEW ACTIVE OFFERS
    # -------------------------------------------------
    offers = agent.view_available_offers()
    print_test("Only active offers returned", len(offers) == 2)

    # -------------------------------------------------
    # TEST 15: GET USER LOYALTY STATUS
    # -------------------------------------------------
    status = agent.get_user_loyalty_status("USER01")
    print_test("Loyalty status fetched", "points" in status and "tier" in status)

    print("\n🎉 ALL TESTS EXECUTED 🎉")


if __name__ == "__main__":
    run_all_tests()
