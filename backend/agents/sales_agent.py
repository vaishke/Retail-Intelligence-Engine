# agents/sales_agent.py
from services.session_service import create_session, get_session, update_session, end_session
from agents.recommendation_agent import RecommendationAgent
from agents.inventory_agent import InventoryAgent
from agents.offer_loyalty_agent import OfferLoyaltyAgent
from agents.fulfillment_agent import FulfillmentAgent
from agents.payment_agent import PaymentAgent
from agents.post_purchase_agent import PostPurchaseAgent

class SalesAgent:
    def __init__(self):
        self.loyalty_agent = OfferLoyaltyAgent()

    # --- Session Handling ---
    def start_session(self, user_id, channel):
        return create_session(user_id, channel)

    def get_session(self, session_id):
        return get_session(session_id)

    def update_session(self, session_id, updates):
        session = get_session(session_id)
        session['context'].update(updates)
        return update_session(session_id, session['context'])

    def end_session(self, session_id):
        return end_session(session_id)

    # --- Recommendations ---
    def recommend_products(self, session_id, constraints=None):
        session = get_session(session_id)
        exclude_ids = session['context'].get('selected_products', [])
        recommendations = RecommendationAgent.recommend_products(
            user_id=session['user_id'],
            constraints=constraints or {},
            top_k=5,
            exclude_product_ids=exclude_ids
        )
        session['context']['recommendations'] = recommendations
        update_session(session_id, session['context'])
        return recommendations

    # --- Inventory ---
    def check_inventory(self, session_id, store_id=None):
        session = get_session(session_id)
        stock_results = []
        for item in session['context'].get('selected_products', []):
            stock_results.append(InventoryAgent.check_stock(item.get("product_id"), store_id))
        session['context']['stock_status'] = stock_results
        update_session(session_id, session['context'])
        return stock_results

    # --- Checkout: Loyalty + Fulfillment ---
    def checkout(self, session_id, coupon_code=None, use_points=0, store_location=None, fulfillment_type="SHIP_TO_HOME"):
        session = get_session(session_id)
        cart_items = session['context'].get('selected_products', [])

        # Ensure cart_items have product_id, qty, price
        formatted_cart = [{"product_id": item["product_id"], "qty": item.get("qty", 1), "price": item["price"]} for item in cart_items]

        # 1️⃣ Process loyalty/coupon
        loyalty_response = self.loyalty_agent.process_checkout(
            user_id=session['user_id'],
            cart_items=formatted_cart,
            coupon_code=coupon_code,
            use_points=use_points
        )

        # Add final_amount and order_id to context
        session['context']['final_amount'] = loyalty_response['final_amount']
        session['context']['cart_order_id'] = loyalty_response['order_id']
        update_session(session_id, session['context'])

        # 2️⃣ Fulfillment
        fulfillment_input = {
            "user_id": session['user_id'],
            "items": formatted_cart,
            "store_location": store_location,
            "fulfillment_type": fulfillment_type,
            "order_id": loyalty_response['order_id']
        }
        fulfillment_response = FulfillmentAgent.process_order(fulfillment_input)
        session['context']['fulfillment'] = fulfillment_response
        update_session(session_id, session['context'])

        return {
            "loyalty": loyalty_response,
            "fulfillment": fulfillment_response
        }

    # --- Payment ---
    def process_payment(self, session_id, payment_method, details=None):
        session = get_session(session_id)
        order_id = session['context'].get('cart_order_id')
        payment_result = PaymentAgent.process_payment(order_id, payment_method, details)
        session['context']['payment_status'] = payment_result.get('success')
        session['context']['transaction_id'] = payment_result.get('transaction_id')
        update_session(session_id, session['context'])
        return payment_result

    # --- Post-Purchase ---
    def post_purchase(self, session_id, delivery_address):
        session = get_session(session_id)
        cart_items = session['context'].get('selected_products', [])
        formatted_cart = [{"product_id": item["product_id"], "qty": item.get("qty", 1), "price": item["price"]} for item in cart_items]

        input_json = {
            "order_id": session['context'].get('cart_order_id'),
            "transaction_id": session['context'].get('transaction_id'),
            "user_id": session['user_id'],
            "cart_items": formatted_cart,
            "final_amount": session['context'].get('final_amount', 0),
            "delivery_address": delivery_address
        }
        result = PostPurchaseAgent.handle_post_purchase(input_json)
        self.end_session(session_id)
        return result