from agents.post_purchase_agent import PostPurchaseAgent

class PostPurchaseService:

    @staticmethod
    def handle_post_service(input_json: dict):
        return PostPurchaseAgent.handle_post_purchase(input_json)
