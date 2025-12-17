from typing import TypedDict, List, Dict, Optional, Any

class CartItem(TypedDict):
    sku: str
    quantity: int

class SalesState(TypedDict, total=False):
    session_id: str
    user_id: str
    user_location: Optional[str]

    intent: Optional[str]
    last_step: Optional[str]
    error: Optional[str]

    constraints: Dict[str, Any]
    recommendations: List[Dict[str, Any]]

    cart_items: List[CartItem]

    inventory_status: Dict[str, Any]

    offers_applied: Dict[str, Any]
    final_amount: Optional[float]

    payment_status: Dict[str, Any]
    transaction_id: Optional[str]

    order_id: Optional[str]
    fulfillment_status: Dict[str, Any]

    shipment_id: Optional[str]
    invoice_id: Optional[str]
