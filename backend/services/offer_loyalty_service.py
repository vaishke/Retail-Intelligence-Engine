from agents.offer_loyalty_agent import OfferLoyaltyAgent

class OfferLoyaltyService:
    agent = OfferLoyaltyAgent()

    @staticmethod
    def checkout_service(user_id, cart_items, coupon_code=None, use_points=0):
        return OfferLoyaltyService.agent.process_checkout(
            user_id=user_id,
            cart_items=cart_items,
            coupon_code=coupon_code,
            use_points=use_points
        )

    @staticmethod
    def get_loyalty_status_service(user_id):
        return OfferLoyaltyService.agent.get_user_loyalty_status(user_id)

    @staticmethod
    def view_offers_service():
        return OfferLoyaltyService.agent.view_available_offers()
