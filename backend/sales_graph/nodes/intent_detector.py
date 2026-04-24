from typing import Dict, Any
import os
import re

from sales_graph.conversation_ai import get_recent_chat_turns, infer_intent_with_groq
from services.recommendation_state_service import (
    extract_state_updates as extract_recommendation_state_updates,
    get_missing_recommendation_fields,
    has_recommendation_context,
)
from services.session_service import get_recommendation_state


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

    raw_message = state.get("latest_user_message", "")
    message = raw_message.lower()
    recent_turns = get_recent_chat_turns(state.get("session_id"))
    fallback_entities = extract_entities_rules(message)

    if os.getenv("GROQ_API_KEY"):
        try:
            llm_result = classify_with_groq(raw_message, state, recent_turns)
            if llm_result:
                intent = str(llm_result.get("intent") or "general_query")
                entities = _merge_detected_entities(llm_result.get("entities") or {}, fallback_entities)
                conversation_act = llm_result.get("conversation_act") or infer_conversation_act(message, state)
                intent_confidence = _normalize_confidence(llm_result.get("confidence"))
            else:
                intent = classify_intent_rules(message)
                entities = fallback_entities
                conversation_act = infer_conversation_act(message, state)
                intent_confidence = 0.45
        except Exception as e:
            print(f"Groq failed, fallback: {e}")
            intent = classify_intent_rules(message)
            entities = fallback_entities
            conversation_act = infer_conversation_act(message, state)
            intent_confidence = 0.35
    else:
        intent = classify_intent_rules(message)
        entities = fallback_entities
        conversation_act = infer_conversation_act(message, state)
        intent_confidence = 0.35

    intent, entities, conversation_act = resolve_dialogue_context(
        message=message,
        state=state,
        intent=intent,
        entities=entities,
        conversation_act=conversation_act,
        confidence=intent_confidence,
    )

    # 🔥 CRITICAL FIX: remove None values (prevents stale state pollution)
    cleaned_entities = {k: v for k, v in entities.items() if v is not None}

    print("DEBUG intent_entities (cleaned):", cleaned_entities)

    return {
        "current_intent": intent,
        "intent_entities": cleaned_entities,  # <-- CLEAN STATE ONLY
        "conversation_act": conversation_act,
        "intent_confidence": intent_confidence,
    }


def classify_with_groq(message: str, state: Dict[str, Any], recent_turns: list[Dict[str, str]]) -> Dict[str, Any] | None:
    return infer_intent_with_groq(message, INTENT_TAXONOMY, state, recent_turns)


# ═══════════════════════════════════════
# RULE-BASED INTENT
# ═══════════════════════════════════════

def classify_intent_rules(message: str) -> str:
    has_checkout_words = any(w in message for w in ["buy", "checkout", "pay", "order"])
    has_checkout_confirmation_words = any(w in message for w in ["yes", "confirm", "proceed"])
    has_payment_words = any(w in message for w in ["upi", "card", "cash", "cash on delivery", "cod"])
    has_tracking_words = any(w in message for w in ["track", "status", "delivery", "shipment", "where is my order", "order status"])
    has_recent_order_words = any(
        w in message
        for w in ["recent orders", "my orders", "show orders", "past orders", "previous orders", "latest orders"]
    )
    has_checkout_followup_words = any(
        w in message
        for w in ["payment", "pay now", "continue payment", "go to payment", "complete payment"]
    )

    if any(w in message for w in ["show my cart", "view my cart", "what is in my cart", "what's in my cart", "open my cart"]):
        return "view_cart"

    if "cart" in message and any(w in message for w in ["remove", "delete"]):
        return "remove_from_cart"

    if "cart" in message and any(w in message for w in ["add", "put"]):
        return "add_to_cart"

    if has_recent_order_words:
        return "order_tracking"

    if has_tracking_words and "order" in message:
        return "order_tracking"

    if has_checkout_followup_words and not has_payment_words:
        return "checkout_confirmation"

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

    if has_checkout_words and has_payment_words:
        return "checkout_confirmation"

    if has_payment_words:
        return "payment_method_selection"

    if has_checkout_words:
        if has_checkout_confirmation_words:
            return "checkout_confirmation"
        return "checkout_intent"

    if has_tracking_words:
        return "order_tracking"

    if any(w in message for w in ["return", "refund"]):
        return "return_request"

    return "general_query"


def resolve_dialogue_context(
    message: str,
    state: Dict[str, Any],
    intent: str,
    entities: Dict[str, Any],
    conversation_act: str,
    confidence: float | None,
) -> tuple[str, Dict[str, Any], str]:
    checkout_stage = state.get("checkout_stage")
    checkout_active = checkout_stage in {"summary_ready", "awaiting_payment_method", "payment_in_progress"}
    compact_message = message.strip()
    short_follow_up = len(compact_message.split()) <= 4
    recommendation_state = get_recommendation_state(state.get("session_id"))
    recommendation_updates = extract_recommendation_state_updates(compact_message)
    recommendation_missing_fields = get_missing_recommendation_fields(recommendation_state)
    recommendation_pending = has_recommendation_context(recommendation_state) and bool(recommendation_missing_fields)

    if entities.get("list_orders"):
        return "order_tracking", entities, "follow_up_request"

    if checkout_active and entities.get("payment_method"):
        return "payment_method_selection", entities, "selection"

    if recommendation_pending and (recommendation_updates or short_follow_up):
        enriched_entities = dict(entities)
        for key in ("category", "subcategory", "product_query"):
            if not enriched_entities.get(key) and recommendation_state.get(key):
                enriched_entities[key] = recommendation_state.get(key)

        stored_tags = recommendation_state.get("tags") or []
        if stored_tags:
            merged_tags = []
            for tag in list(enriched_entities.get("tags") or []) + list(stored_tags):
                if isinstance(tag, str) and tag not in merged_tags:
                    merged_tags.append(tag)
            if merged_tags:
                enriched_entities["tags"] = merged_tags

        if "price_range" not in enriched_entities:
            price_min = recommendation_state.get("price_min")
            price_max = recommendation_state.get("price_max")
            if price_min is not None or price_max is not None:
                enriched_entities["price_range"] = [
                    0 if price_min is None else price_min,
                    10 ** 9 if price_max is None else price_max,
                ]

        if not recommendation_updates and compact_message in {"yes", "yes please", "go ahead", "continue"}:
            return "discovery", enriched_entities, "follow_up_request"

        return "refine_recommendations", enriched_entities, "follow_up_request"

    if confidence is not None and confidence >= 0.7:
        return intent, entities, conversation_act

    if checkout_active and short_follow_up:
        if compact_message in {"payment", "pay", "continue", "continue payment", "proceed payment", "pay now"}:
            return "checkout_confirmation", entities, "follow_up_request"
        if compact_message in {"yes", "yes please", "go ahead", "continue checkout", "proceed"}:
            return "checkout_confirmation", entities, "confirmation"

    if state.get("last_worker") == "post_purchase_agent" and any(
        phrase in compact_message for phrase in ["show orders", "my orders", "recent orders", "past orders"]
    ):
        entities = {**entities, "list_orders": True}
        return "order_tracking", entities, "follow_up_request"

    if short_follow_up and compact_message in {"this one", "that one", "add this", "add it"}:
        entities = {**entities, "reference": "recent_item"}
        return "add_to_cart", entities, "selection"

    return intent, entities, conversation_act


def _merge_detected_entities(primary: Dict[str, Any], fallback: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(primary or {})

    for key, value in (fallback or {}).items():
        if key not in merged or merged.get(key) in (None, "", [], {}):
            merged[key] = value

    if isinstance(merged.get("tags"), list) and isinstance(fallback.get("tags"), list):
        combined_tags = []
        for tag in merged["tags"] + fallback["tags"]:
            if isinstance(tag, str) and tag not in combined_tags:
                combined_tags.append(tag)
        merged["tags"] = combined_tags

    return merged


def infer_conversation_act(message: str, state: Dict[str, Any]) -> str:
    normalized = message.strip().lower()
    if normalized in {"yes", "yes please", "go ahead", "confirm", "proceed"}:
        return "confirmation"

    if any(term in normalized for term in ["upi", "card", "cash on delivery", "cod", "cash"]):
        return "selection"

    if len(normalized.split()) <= 4 and state.get("last_worker"):
        return "follow_up_request"

    if any(term in normalized for term in ["actually", "instead", "change", "not this"]):
        return "correction"

    return "new_request"


def _normalize_confidence(value: Any) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.5
    return max(0.0, min(1.0, confidence))


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

    order_id_match = re.search(r"\b[a-f0-9]{24}\b", message)
    if order_id_match:
        entities["order_id"] = order_id_match.group(0)

    if any(
        phrase in message
        for phrase in ["recent orders", "my orders", "show orders", "past orders", "previous orders", "latest orders"]
    ):
        entities["list_orders"] = True

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
