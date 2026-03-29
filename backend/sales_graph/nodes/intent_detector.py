"""
sales_graph/nodes/intent_detector.py

Intent classification node with TWO options:
1. Rule-based (fast, free, deterministic) - DEFAULT
2. Groq LLM-based (accurate, still free, requires API key)

To use Groq: Set environment variable GROQ_API_KEY
"""

from typing import Dict, Any
import os


# Intent taxonomy from design doc Section 8.1
INTENT_TAXONOMY = [
    "discovery",                # User wants product suggestions
    "refine_recommendations",   # Filter or modify suggestions
    "availability_check",       # Check if items in stock
    "reservation_request",      # Reserve items in-store
    "offer_inquiry",            # Ask about discounts/loyalty
    "checkout_intent",          # Initiate payment
    "checkout_confirmation",    # Confirm after seeing summary
    "payment_method_selection", # Select/change payment method
    "order_tracking",           # Status of past order
    "return_request",           # Return or exchange
    "general_query"             # Out of scope / clarification needed
]


def intent_detector_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classifies the user's latest message into an intent.
    
    Auto-detects which method to use:
    - If GROQ_API_KEY is set: uses Groq LLM (accurate)
    - Otherwise: uses rule-based classification (fast, free)
    
    Updates:
    - state["current_intent"]
    - state["intent_entities"]
    """
    
    message = state.get("latest_user_message", "").lower()
    
    # Check if Groq API key is available
    if os.getenv("GROQ_API_KEY"):
        try:
            intent, entities = classify_with_groq(message)
        except Exception as e:
            print(f"Groq classification failed, falling back to rules: {e}")
            intent = classify_intent_rules(message)
            entities = extract_entities_rules(message, state)
    else:
        # Use rule-based classification
        intent = classify_intent_rules(message)
        entities = extract_entities_rules(message, state)
    
    return {
        "current_intent": intent,
        "intent_entities": entities
    }


# ═══════════════════════════════════════════════════════════════════
# OPTION 1: RULE-BASED CLASSIFICATION (DEFAULT, FREE)
# ═══════════════════════════════════════════════════════════════════

def classify_intent_rules(message: str) -> str:
    """
    Rule-based intent classification using keyword matching.
    Fast, free, deterministic.
    """
    
    # Discovery keywords
    if any(word in message for word in ["show", "recommend", "suggest", "want", "looking for", "find me", "need"]):
        return "discovery"
    
    # Refinement keywords
    if any(word in message for word in ["more", "different", "filter", "under", "cheaper", "expensive", "other"]):
        return "refine_recommendations"
    
    # Availability check
    if any(word in message for word in ["stock", "available", "in store", "inventory", "have this", "availability"]):
        return "availability_check"
    
    # Reservation
    if any(word in message for word in ["reserve", "hold", "keep", "book", "try on", "save for me"]):
        return "reservation_request"
    
    # Offers
    if any(word in message for word in ["discount", "offer", "coupon", "points", "loyalty", "deal", "promo"]):
        return "offer_inquiry"
    
    # Checkout
    if any(word in message for word in ["buy", "purchase", "checkout", "pay", "order"]):
        # Distinguish between intent and confirmation
        if any(word in message for word in ["yes", "confirm", "proceed", "go ahead", "sure"]):
            return "checkout_confirmation"
        return "checkout_intent"
    
    # Payment method
    if any(word in message for word in ["upi", "card", "cash", "payment method", "credit", "debit"]):
        return "payment_method_selection"
    
    # Tracking
    if any(word in message for word in ["track", "where is", "status", "delivery", "shipped", "order status"]):
        return "order_tracking"
    
    # Returns
    if any(word in message for word in ["return", "exchange", "refund", "send back"]):
        return "return_request"
    
    # Default
    return "general_query"


def extract_entities_rules(message: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts entities from the message using simple rules.
    """
    
    entities = {
        "product_query": None,
        "location": None,
        "order_id": None,
        "sku_list": None,
        "price_range": None,
        "category": None,
        "subcategory": None,
        "tags": None,
        "color": None
    }
    
    # Extract product query
    triggers = ["want", "show me", "looking for", "find", "recommend", "need"]
    for trigger in triggers:
        if trigger in message:
            parts = message.split(trigger, 1)
            if len(parts) > 1:
                entities["product_query"] = parts[1].strip()
                break
    
    # Extract price range
    if "under" in message:
        try:
            price_str = message.split("under")[1].strip().split()[0]
            max_price = int(''.join(filter(str.isdigit, price_str)))
            entities["price_range"] = [0, max_price]
        except:
            pass
    
    # Extract color
    colors = ["red", "blue", "green", "black", "white", "yellow", "pink", "purple", "orange", "brown", "grey", "gray"]
    for color in colors:
        if color in message:
            entities["color"] = color
            break
    
    # Extract category
    categories = ["clothing", "electronics", "accessories", "footwear", "kurti", "saree", "shirt", "dress"]
    for cat in categories:
        if cat in message:
            entities["category"] = cat
            break

    # Extract subcategory
    subcategory_map = {
        "anarkali": "Ethnic Wear",
        "kurti": "Ethnic Wear",
        "kurta": "Ethnic Wear",
        "saree": "Ethnic Wear",
        "lehenga": "Ethnic Wear",
        "salwar": "Ethnic Wear",
        "jacket": "Jackets",
        "cardigan": "Sweaters",
        "sweater": "Sweaters",
        "top": "Tops",
        "blouse": "Tops",
        "jeans": "Jeans",
        "denim": "Jeans",
        "dress": "Dresses",
        "skirt": "Skirts",
        "shirt": "Shirts",
        "tshirt": "T-Shirts",
        "t-shirt": "T-Shirts",
    }
    for keyword, subcat in subcategory_map.items():
        if keyword in message:
            entities["subcategory"] = subcat
            break

    # Extract style tags
    style_keywords = [
        "anarkali", "printed", "embroidered", "silk", "denim", "sequin",
        "woolen", "ethnic", "casual", "formal", "party wear", "festive",
        "floral", "plain", "striped", "checked", "solid", "lace", "velvet"
    ]
    matched_tags = [tag for tag in style_keywords if tag in message]
    entities["tags"] = matched_tags if matched_tags else None
    
    return entities


# ═══════════════════════════════════════════════════════════════════
# OPTION 2: GROQ LLM-BASED CLASSIFICATION (ACCURATE, FREE)
# ═══════════════════════════════════════════════════════════════════

def classify_with_groq(message: str) -> tuple[str, Dict[str, Any]]:
    """
    Uses Groq API for intent classification.
    Groq provides free, fast LLM inference.
    
    Requires: pip install groq
    Environment variable: GROQ_API_KEY
    """
    
    from groq import Groq
    import json
    
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    prompt = f"""Classify this user message into ONE intent from the list below.
Also extract relevant entities.

User message: "{message}"

Valid intents:
{', '.join(INTENT_TAXONOMY)}

Extract entities if present:
- product_query: what product they want (string or null)
- location: city/store if mentioned (string or null)
- price_range: [min, max] if mentioned (array or null)
- category: broad product category e.g. "Clothing", "Electronics" (string or null)
- subcategory: specific subcategory e.g. "Ethnic Wear", "Jackets", "Tops", "Jeans" (string or null)
- tags: style/attribute keywords e.g. ["anarkali", "printed", "silk", "casual"] (array or null)
- color: color if mentioned (string or null)

Return ONLY valid JSON in this exact format (no markdown, no extra text):
{{
  "intent": "<intent_name>",
  "entities": {{
    "product_query": "...",
    "price_range": [min, max],
    "category": "...",
    "subcategory": "...",
    "tags": [...],
    "color": "..."
  }}
}}"""
    
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",  # Fast, free Groq model
        messages=[{"role": "user", "content": prompt}],
        temperature=0,  # Deterministic output
        max_tokens=200
    )
    
    result_text = response.choices[0].message.content.strip()
    
    # Parse JSON response
    try:
        result = json.loads(result_text)
        intent = result.get("intent", "general_query")
        entities = result.get("entities", {})
        
        # Validate intent is in taxonomy
        if intent not in INTENT_TAXONOMY:
            intent = "general_query"
        
        return intent, entities
    
    except json.JSONDecodeError:
        # Fallback to rule-based if JSON parsing fails
        print(f"Groq returned invalid JSON: {result_text}")
        return classify_intent_rules(message), extract_entities_rules(message, {})


# ═══════════════════════════════════════════════════════════════════
# USAGE INSTRUCTIONS
# ═══════════════════════════════════════════════════════════════════

"""
SETUP FOR GROQ (RECOMMENDED):

1. Install Groq SDK:
   pip install groq

2. Get free API key from: https://console.groq.com/keys

3. Set environment variable:
   export GROQ_API_KEY="your-key-here"
   
   Or in Python:
   os.environ["GROQ_API_KEY"] = "your-key-here"

4. That's it! The node will auto-detect and use Groq.

FALLBACK:
If GROQ_API_KEY is not set, the node uses rule-based classification (no API needed).
"""