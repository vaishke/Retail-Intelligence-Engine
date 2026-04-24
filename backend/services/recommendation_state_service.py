import re
from copy import deepcopy


DEFAULT_RECOMMENDATION_STATE = {
    "category": None,
    "price_min": None,
    "price_max": None,
    "occasion": None,
}

OCCASION_KEYWORDS = {
    "wedding",
    "party",
    "casual",
    "formal",
    "office",
    "festival",
    "festive",
    "travel",
    "gym",
    "running",
    "workout",
    "daily",
    "college",
    "beach",
    "date",
}

CATEGORY_ALIASES = {
    "women": {"product_category": "Fashion", "tags": ["women"]},
    "woman": {"product_category": "Fashion", "tags": ["women"]},
    "ladies": {"product_category": "Fashion", "tags": ["women"]},
    "female": {"product_category": "Fashion", "tags": ["women"]},
    "men": {"product_category": "Fashion", "tags": ["men"]},
    "man": {"product_category": "Fashion", "tags": ["men"]},
    "male": {"product_category": "Fashion", "tags": ["men"]},
    "kids": {"product_category": "Fashion", "tags": ["kids"]},
    "children": {"product_category": "Fashion", "tags": ["kids"]},
    "boys": {"product_category": "Fashion", "tags": ["boys"]},
    "girls": {"product_category": "Fashion", "tags": ["girls"]},
    "fashion": {"product_category": "Fashion", "tags": []},
    "footwear": {"product_category": "Footwear", "tags": []},
    "shoes": {"product_category": "Footwear", "tags": ["shoes"]},
    "beauty": {"product_category": "Beauty", "tags": []},
    "electronics": {"product_category": "Electronics", "tags": []},
    "home": {"product_category": "Home", "tags": []},
}


def initialize_recommendation_state(raw_state=None):
    state = deepcopy(DEFAULT_RECOMMENDATION_STATE)
    if isinstance(raw_state, dict):
        for key in state:
            if key in raw_state:
                state[key] = raw_state.get(key)
    return state


def extract_state_updates(message):
    text = str(message or "").strip()
    normalized_text = text.lower()
    updates = {}

    category = _extract_category(normalized_text)
    if category:
        updates["category"] = category

    occasion = _extract_occasion(normalized_text)
    if occasion:
        updates["occasion"] = occasion

    price_update = _extract_price_range(normalized_text)
    if price_update is not None:
        updates["price_min"] = price_update.get("price_min")
        updates["price_max"] = price_update.get("price_max")
        updates["_replace_price"] = True

    return updates


def merge_recommendation_state(existing_state, detected_updates):
    state = initialize_recommendation_state(existing_state)
    updates = dict(detected_updates or {})

    replace_price = updates.pop("_replace_price", False)
    if replace_price:
        state["price_min"] = updates.pop("price_min", None)
        state["price_max"] = updates.pop("price_max", None)

    for key in ("category", "occasion", "price_min", "price_max"):
        if key in updates:
            state[key] = updates[key]

    return state


def build_recommendation_filters(state):
    normalized_state = initialize_recommendation_state(state)
    filters = {}
    tags = []

    category = normalized_state.get("category")
    if category:
        category_mapping = CATEGORY_ALIASES.get(category.lower())
        if category_mapping:
            filters["category"] = category_mapping["product_category"]
            tags.extend(category_mapping.get("tags", []))
        else:
            filters["category"] = category

    price_min = normalized_state.get("price_min")
    price_max = normalized_state.get("price_max")
    if price_min is not None or price_max is not None:
        filters["price_range"] = [
            0 if price_min is None else price_min,
            10 ** 9 if price_max is None else price_max,
        ]

    occasion = normalized_state.get("occasion")
    if occasion:
        tags.append(occasion)

    if tags:
        filters["tags"] = list(dict.fromkeys(tags))

    return filters


def build_recommendation_input(user_query, state):
    return {
        "user_query": user_query,
        "state": initialize_recommendation_state(state),
    }


def get_missing_recommendation_fields(state):
    normalized_state = initialize_recommendation_state(state)
    missing = []

    if not normalized_state.get("category"):
        missing.append("category")

    if normalized_state.get("price_min") is None and normalized_state.get("price_max") is None:
        missing.append("price")

    if not normalized_state.get("occasion"):
        missing.append("occasion")

    return missing


def build_missing_fields_prompt(missing_fields):
    questions = {
        "category": "Which category are you shopping for, like women, men, kids, fashion, or electronics?",
        "price": "What budget should I stay within?",
        "occasion": "What occasion or use-case is this for, like casual, office, party, or wedding?",
    }
    prompts = [questions[field] for field in missing_fields if field in questions]
    return " ".join(prompts)


def _extract_category(text):
    for alias in CATEGORY_ALIASES:
        if re.search(rf"\b{re.escape(alias)}\b", text):
            canonical = "women" if alias in {"woman", "ladies", "female"} else alias
            canonical = "men" if alias in {"man", "male"} else canonical
            canonical = "kids" if alias in {"children"} else canonical
            return canonical
    return None


def _extract_occasion(text):
    for occasion in OCCASION_KEYWORDS:
        if re.search(rf"\b{re.escape(occasion)}\b", text):
            return "festival" if occasion == "festive" else occasion
    return None


def _extract_price_range(text):
    numbers = [int(match.replace(",", "")) for match in re.findall(r"\b\d[\d,]*\b", text)]
    if not numbers:
        return None

    between_match = re.search(
        r"(?:between|from)\s+(\d[\d,]*)\s+(?:and|to|-)\s+(\d[\d,]*)",
        text,
    )
    if between_match:
        return {
            "price_min": int(between_match.group(1).replace(",", "")),
            "price_max": int(between_match.group(2).replace(",", "")),
        }

    under_match = re.search(r"(?:under|below|less than|max(?:imum)? of)\s+(\d[\d,]*)", text)
    if under_match:
        return {
            "price_min": None,
            "price_max": int(under_match.group(1).replace(",", "")),
        }

    over_match = re.search(r"(?:above|over|more than|starting from)\s+(\d[\d,]*)", text)
    if over_match:
        return {
            "price_min": int(over_match.group(1).replace(",", "")),
            "price_max": None,
        }

    if len(numbers) >= 2:
        return {
            "price_min": min(numbers[0], numbers[1]),
            "price_max": max(numbers[0], numbers[1]),
        }

    return {
        "price_min": None,
        "price_max": numbers[0],
    }
