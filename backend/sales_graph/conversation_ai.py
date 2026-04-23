from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv()

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def get_recent_chat_turns(session_id: str | None, limit: int = 6) -> List[Dict[str, str]]:
    if not session_id:
        return []

    try:
        from db.database import sessions_collection

        session = sessions_collection.find_one({"_id": session_id}, {"chat_history": 1})
    except Exception:
        return []

    if not session:
        return []

    chat_history = session.get("chat_history", [])
    recent_turns = []
    for entry in chat_history[-limit:]:
        role = entry.get("role")
        message = entry.get("message")
        if role and message:
            recent_turns.append({"role": role, "message": str(message)})

    return recent_turns


def summarize_state_for_model(state: Dict[str, Any]) -> Dict[str, Any]:
    checkout_context = state.get("loyalty_data") or state.get("checkout_context") or {}
    order_status = state.get("order_status") or {}
    return {
        "checkout_stage": state.get("checkout_stage"),
        "cart_items": [
            {
                "name": item.get("name"),
                "qty": item.get("qty", 1),
                "price": item.get("price"),
            }
            for item in state.get("cart_items", [])[:5]
        ],
        "recommended_items": [
            item.get("name")
            for item in state.get("recommended_items", [])[:5]
        ],
        "payment_method": state.get("payment_method"),
        "final_amount": checkout_context.get("final_amount"),
        "last_worker": state.get("last_worker"),
        "last_intent": state.get("current_intent"),
        "last_order_id": order_status.get("order_id"),
        "tracking_status": order_status.get("tracking_status"),
    }


def infer_intent_with_groq(
    message: str,
    taxonomy: List[str],
    state: Dict[str, Any],
    recent_turns: List[Dict[str, str]],
) -> Dict[str, Any] | None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    system_prompt = (
        "You classify ecommerce assistant messages.\n"
        "Return only JSON with keys: intent, entities, conversation_act, confidence.\n"
        f"Valid intents: {', '.join(taxonomy)}.\n"
        "Use conversation context to resolve short follow-ups like 'payment', 'yes', 'this one', or 'show my orders'.\n"
        "Map order-history and tracking requests to order_tracking.\n"
        "Map continuing-checkout confirmations to checkout_confirmation.\n"
        "Map payment method choices like UPI/card/cash on delivery to payment_method_selection.\n"
        "Set confidence between 0 and 1.\n"
        "entities must be an object and conversation_act must be one of: new_request, follow_up_request, confirmation, selection, correction, chitchat."
    )

    user_prompt = json.dumps(
        {
            "latest_user_message": message,
            "recent_turns": recent_turns[-6:],
            "state": summarize_state_for_model(state),
        },
        ensure_ascii=True,
    )

    payload = {
        "model": DEFAULT_GROQ_MODEL,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    return _post_groq_json(payload, api_key)


def style_sales_response(
    response: Dict[str, Any],
    state: Dict[str, Any],
    recent_turns: List[Dict[str, str]],
) -> Dict[str, Any]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return response

    message = response.get("message")
    prompt = response.get("prompt")
    if not message:
        return response

    system_prompt = (
        "You are rewriting ecommerce assistant replies to sound like a warm, polished retail salesperson.\n"
        "Return only JSON with keys: message and prompt.\n"
        "Do not change facts, prices, IDs, product names, payment methods, counts, or order status.\n"
        "Keep it concise, helpful, and natural.\n"
        "Do not add information not already present.\n"
        "If prompt is null, return null for prompt."
    )
    user_prompt = json.dumps(
        {
            "response": {"message": message, "prompt": prompt},
            "state": summarize_state_for_model(state),
            "recent_turns": recent_turns[-4:],
        },
        ensure_ascii=True,
    )

    payload = {
        "model": DEFAULT_GROQ_MODEL,
        "temperature": 0.4,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    styled = _post_groq_json(payload, api_key)
    if not styled:
        return response

    updated = dict(response)
    if styled.get("message"):
        updated["message"] = styled["message"]
    if "prompt" in styled:
        updated["prompt"] = styled["prompt"]
    return updated


def _post_groq_json(payload: Dict[str, Any], api_key: str) -> Dict[str, Any] | None:
    request = urllib.request.Request(
        GROQ_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=6) as response:
            body = response.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError, ValueError):
        return None

    try:
        raw = json.loads(body)
        content = raw["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return None

    return _extract_json_object(content)


def _extract_json_object(text: str) -> Dict[str, Any] | None:
    if not text:
        return None

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None

    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None

    return parsed if isinstance(parsed, dict) else None
