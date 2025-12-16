from agents.post_purchase_agent import PostPurchaseAgent

class PostPurchaseService:
    def handle_post_service(input_json):
        return PostPurchaseAgent.handle_post_purchase(input_json)