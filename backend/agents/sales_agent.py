# agents/sales_agent.py
from services.session_service import create_session, get_session, update_session, end_session
from agents.recommendation_agent import RecommendationAgent
from agents.inventory_agent import InventoryAgent
from agents.payment_agent import PaymentAgent
from agents.post_purchase_agent import PostPurchaseAgent

class SalesAgent:

    # --- Session handling ---
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

    # --- Recommendation ---
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
    def check_inventory(self, session_id, user_location):
        session = get_session(session_id)
        stock_results = []
        for sku in session['context'].get('selected_products', []):
            stock_results.append(InventoryAgent.check_stock(sku, user_location))
        session['context']['stock_status'] = stock_results
        update_session(session_id, session['context'])
        return stock_results

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
        input_json = {
            "order_id": session['context'].get('cart_order_id'),
            "transaction_id": session['context'].get('transaction_id'),
            "user_id": session['user_id'],
            "cart_items": [{"sku": sku, "quantity": 1} for sku in session['context'].get('selected_products', [])],
            "final_amount": session['context'].get('final_amount', 0),
            "delivery_address": delivery_address
        }
        result = PostPurchaseAgent.handle_post_purchase(input_json)
        self.end_session(session_id)
        return result
