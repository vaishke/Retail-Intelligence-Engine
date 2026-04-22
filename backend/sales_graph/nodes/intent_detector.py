from typing import Dict, Any
import os
import re


INTENT_TAXONOMY = [
    "discovery",
    "refine_recommendations",
    "add_to_cart",
    "view_cart",
    "remove_from_cart",
    "availability_check",
    "reservation_request",
    "offer_inquiry",
    "checkout_intent",
    "checkout_confirmation",
    "payment_method_selection",
    "order_tracking",
    "return_request",
    "general_query"
]


def intent_detector_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean intent + entity extraction with HARD RESET of entities.
    """

    message = state.get("latest_user_message", "").lower()

    if os.getenv("GROQ_API_KEY"):
        try:
            intent, entities = classify_with_groq(message)
        except Exception as e:
            print(f"Groq failed, fallback: {e}")
            intent = classify_intent_rules(message)
            entities = extract_entities_rules(message)
    else:
        intent = classify_intent_rules(message)
        entities = extract_entities_rules(message)

    # 🔥 CRITICAL FIX: remove None values (prevents stale state pollution)
    cleaned_entities = {k: v for k, v in entities.items() if v is not None}

    print("DEBUG intent_entities (cleaned):", cleaned_entities)

    return {
        "current_intent": intent,
        "intent_entities": cleaned_entities  # <-- CLEAN STATE ONLY
    }


# ═══════════════════════════════════════
# RULE-BASED INTENT
# ═══════════════════════════════════════

def classify_intent_rules(message: str) -> str:
    if any(w in message for w in ["show my cart", "view my cart", "what is in my cart", "what's in my cart", "open my cart"]):
        return "view_cart"

    if "cart" in message and any(w in message for w in ["remove", "delete"]):
        return "remove_from_cart"

    if "cart" in message and any(w in message for w in ["add", "put"]):
        return "add_to_cart"

    discovery_triggers = [
        "show",
        "show me",
        "recommend",
        "recommend me",
        "suggest",
        "can you suggest",
        "want",
        "i want",
        "looking for",
        "find me",
        "need",
        "give me",
        "browse",
        "anything in",
    ]
    if any(w in message for w in discovery_triggers):
        return "discovery"

    if any(w in message for w in ["more", "different", "filter", "under", "cheaper", "expensive", "other"]):
        return "refine_recommendations"

    if any(w in message for w in ["stock", "available", "inventory"]):
        return "availability_check"

    if any(w in message for w in ["reserve", "hold", "book"]):
        return "reservation_request"

    if any(w in message for w in ["discount", "offer", "coupon", "deal"]):
        return "offer_inquiry"

    if any(w in message for w in ["payment mode", "payment method", "do payment", "make payment"]):
        return "payment_method_selection"

    if any(w in message for w in ["upi", "card", "cash"]):
        return "payment_method_selection"

    if any(w in message for w in ["buy", "checkout", "pay", "order"]):
        if any(w in message for w in ["yes", "confirm", "proceed"]):
            return "checkout_confirmation"
        return "checkout_intent"

    if any(w in message for w in ["track", "status", "delivery"]):
        return "order_tracking"

    if any(w in message for w in ["return", "refund"]):
        return "return_request"

    return "general_query"


# ═══════════════════════════════════════
# ENTITY EXTRACTION (FIXED)
# ═══════════════════════════════════════

def extract_entities_rules(message: str) -> Dict[str, Any]:

    entities = {}
    quantity = extract_quantity(message)
    if quantity is not None:
        entities["quantity"] = quantity

    if any(ref in message for ref in ["this", "that", "it"]):
        entities["reference"] = "recent_item"

    # Product query
    triggers = [
        "add to cart",
        "add this",
        "add",
        "put this in my cart",
        "put this into my cart",
        "put it in my cart",
        "put",
        "add it to my cart",
        "remove from cart",
        "remove this",
        "remove",
        "show me",
        "looking for",
        "find me",
        "find",
        "recommend me",
        "recommend",
        "can you suggest",
        "suggest",
        "give me",
        "browse",
        "i want",
        "want",
        "need",
    ]
    for trigger in triggers:
        if trigger in message:
            parts = message.split(trigger, 1)
            if len(parts) > 1:
                raw_query = parts[1].strip()
                normalized_query, result_limit = normalize_product_query(raw_query)
                if normalized_query:
                    entities["product_query"] = normalized_query
                if result_limit:
                    entities["result_limit"] = result_limit
                break

    # Price
    if "under" in message:
        try:
            price_str = message.split("under")[1].strip().split()[0]
            max_price = int(''.join(filter(str.isdigit, price_str)))
            entities["price_range"] = [0, max_price]
        except:
            pass

    # Color (FIX: consistent key name)
    colors = ["red", "blue", "green", "black", "white", "yellow", "pink"]
    for color in colors:
        if color in message:
            entities["colors"] = [color]   # <-- FIXED (list + consistent key)
            break

    # Category (normalize casing + synonyms)
    category_aliases = {
        "clothing": "Clothing",
        "clothes": "Clothing",
        "apparel": "Clothing",
        "electronics": "Electronics",
        "electronic": "Electronics",
        "gadgets": "Electronics",
        "accessories": "Accessories",
        "accessory": "Accessories",
        "footwear": "Footwear",
        "shoes": "Footwear",
        "shoe": "Footwear",
        "earbuds": "Electronics",
        "earphones": "Electronics",
        "headphones": "Electronics",
        "bottle": "Accessories",
        "water bottle": "Accessories",
    }
    for alias, category in category_aliases.items():
        if alias in message:
            entities["category"] = category
            break

    # Subcategory
    subcategory_map = {
        "yoga mat": "Fitness",
        "mat": "Fitness",
        "water bottle": "Hydration",
        "bottle": "Hydration",
        "earbuds": "Audio",
        "earphones": "Audio",
        "kurti": "Ethnic Wear",
        "kurta": "Ethnic Wear",
        "ethnic wear": "Ethnic Wear",
        "traditional wear": "Ethnic Wear",
        "indian wear": "Ethnic Wear",
        "saree": "Ethnic Wear",
        "lehenga": "Ethnic Wear",
        "shirt": "Shirts",
        "jeans": "Jeans",
        "dress": "Dresses",
    }

    for keyword, subcat in subcategory_map.items():
        if keyword in message:
            entities["subcategory"] = subcat
            break

    # Tags
    style_keywords = ["ethnic", "casual", "formal", "party", "printed", "wireless", "smart", "fitness", "sports"]
    tags = [tag for tag in style_keywords if tag in message]
    if tags:
        entities["tags"] = tags

    payment_method_map = {
        "upi": "UPI",
        "credit card": "CARD",
        "debit card": "CARD",
        "card": "CARD",
        "cash on delivery": "COD",
        "cod": "COD",
        "cash": "COD",
        "wallet": "WALLET",
        "net banking": "NETBANKING",
        "netbanking": "NETBANKING",
    }
    for keyword, method in payment_method_map.items():
        if keyword in message:
            entities["payment_method"] = method
            break

    return entities


def normalize_product_query(raw_query: str) -> tuple[str, int | None]:
    """
    Extracts a clean product phrase and optional requested result count.
    Examples:
    - "1 yoga mat" -> ("yoga mat", 1)
    - "some ethnic wear" -> ("ethnic wear", None)
    """
    query = raw_query.strip().lower()
    query = re.sub(r"[^\w\s]", " ", query)
    query = re.sub(r"\s+", " ", query).strip()

    result_limit = None
    number_words = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
    }

    match = re.match(r"^(?P<count>\d+|one|two|three|four|five)\s+(?P<query>.+)$", query)
    if match:
        count_text = match.group("count")
        result_limit = int(count_text) if count_text.isdigit() else number_words[count_text]
        query = match.group("query").strip()

    query = re.sub(r"^(some|a|an|any)\s+", "", query).strip()
    query = re.sub(r"\b(please|for me|for us)\b", "", query).strip()
    query = re.sub(r"\b(can you|could you|would you)\b", "", query).strip()
    query = re.sub(r"\b(me|something|anything|products|product|items|item|cart)\b", "", query).strip()
    query = re.sub(r"\b(to my|in my|into my)\b", "", query).strip()
    query = re.sub(r"\b(add|put|remove|delete|pls|plss|please)\b", "", query).strip()
    query = re.sub(r"\s+", " ", query).strip()

    if not query:
        return "", result_limit

    return query, result_limit


def extract_quantity(message: str) -> int | None:
    number_words = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
    }

    quantity_match = re.search(r"\b(\d+)\b", message)
    if quantity_match:
        return max(1, int(quantity_match.group(1)))

    for word, value in number_words.items():
        if re.search(rf"\b{word}\b", message):
            return value

    return None
