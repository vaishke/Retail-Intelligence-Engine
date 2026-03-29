# Sales Graph — LangGraph Orchestration Implementation

## 📋 Overview

This folder contains the **LangGraph orchestration layer** that sits on top of your existing agents. It implements the multi-agent architecture from the design doc (`DesignDocByClaude.md`).

**What it does:**
- Provides intelligent routing between your existing worker agents
- Maintains stateful conversations across channels (web → mobile → kiosk)
- Handles silent chaining (recommendation → inventory automatic flow)
- Implements consent gates (user must confirm before payment)
- Manages retries, error handling, and stale data validation

---

## 📁 File Structure

```
sales_graph/
├── state.py                    # SessionState TypedDict schema
├── graph.py                    # Main LangGraph orchestration
├── nodes/
│   ├── intent_detector.py      # Intent classification (rule-based MVP)
│   ├── sales_planner.py        # Central routing brain
│   ├── recommend.py            # Wrapper around RecommendationAgent
│   ├── inventory.py            # Wrapper around InventoryAgent
│   ├── loyalty_offers.py       # Wrapper around OfferLoyaltyAgent (TODO)
│   ├── payment.py              # Wrapper around PaymentAgent (TODO)
│   ├── fulfilment.py           # Wrapper around FulfillmentAgent (TODO)
│   ├── post_purchase.py        # Wrapper around PostPurchaseAgent (TODO)
│   └── response_generator.py   # Formats responses to user
└── README.md                   # This file
```

---

## ✅ What's Been Built (MVP)

| Component | Status | File |
|---|---|---|
| State schema | ✅ Complete | `state.py` |
| Intent detector (rule-based) | ✅ Complete | `nodes/intent_detector.py` |
| Sales planner (routing brain) | ✅ Complete | `nodes/sales_planner.py` |
| Recommendation wrapper | ✅ Complete | `nodes/recommend.py` |
| Inventory wrapper | ✅ Complete | `nodes/inventory.py` |
| Response generator | ✅ Complete | `nodes/response_generator.py` |
| Main graph | ✅ Complete (missing 4 workers) | `graph.py` |

---

## 🚧 What Still Needs to Be Built

You need to create 4 more worker node wrappers following the same pattern as `recommend.py` and `inventory.py`:

### 1. `nodes/loyalty_offers.py`

```python
from agents.offer_loyalty_agent import OfferLoyaltyAgent
from bson import ObjectId

def loyalty_offers_agent_node(state):
    user_id = ObjectId(state["user_id"])
    cart_items = state["cart_items"]
    
    # Format cart items with ObjectIds
    formatted_cart = [
        {
            "product_id": ObjectId(item["product_id"]),
            "qty": item.get("qty", 1),
            "price": item["price"]
        }
        for item in cart_items
    ]
    
    loyalty_agent = OfferLoyaltyAgent()
    result = loyalty_agent.process_checkout(
        user_id=user_id,
        cart_items=formatted_cart,
        coupon_code=state.get("coupon_code"),  # Add this to state if needed
        use_points=state.get("use_points", 0)
    )
    
    if result.get("success"):
        return {
            "loyalty_data": result,
            "last_worker": "loyalty_offers_agent",
            "agent_call_history": state["agent_call_history"] + ["loyalty_offers_agent"],
            "last_error": None
        }
    else:
        return {
            "last_worker": "loyalty_offers_agent",
            "last_error": {
                "code": "LOYALTY_FAILED",
                "message": result.get("message"),
                "worker": "loyalty_offers_agent",
                "retryable": False
            }
        }
```

### 2. `nodes/payment.py`

```python
from agents.payment_agent import PaymentAgent
from bson import ObjectId
import hashlib
import json

def payment_agent_node(state):
    # Generate idempotency key (design doc Section 12)
    if not state.get("payment_idempotency_key"):
        cart_hash = hashlib.sha256(
            json.dumps(state["cart_items"], sort_keys=True).encode()
        ).hexdigest()[:16]
        idempotency_key = f"{state['session_id']}_{cart_hash}"
    else:
        idempotency_key = state["payment_idempotency_key"]
    
    # Get order_id from loyalty_data
    order_id = state.get("loyalty_data", {}).get("order_id")
    
    result = PaymentAgent.process_payment(
        order_id=order_id,
        payment_method=state.get("payment_method", "UPI"),
        details=state.get("payment_details")
    )
    
    return {
        "payment_status": result,
        "payment_idempotency_key": idempotency_key,
        "last_worker": "payment_agent",
        "agent_call_history": state["agent_call_history"] + ["payment_agent"],
        "last_error": None if result.get("success") else {
            "code": "PAYMENT_FAILED",
            "message": result.get("message"),
            "worker": "payment_agent",
            "retryable": True
        }
    }
```

### 3. `nodes/fulfilment.py`

```python
from agents.fulfillment_agent import FulfillmentAgent
from bson import ObjectId

def fulfilment_agent_node(state):
    order_input = {
        "user_id": ObjectId(state["user_id"]),
        "session_id": ObjectId(state["session_id"]),
        "items": [
            {
                "product_id": ObjectId(item["product_id"]),
                "qty": item["qty"],
                "price": item["price"]
            }
            for item in state["cart_items"]
        ],
        "fulfillment_type": state.get("fulfillment_type", "SHIP_TO_HOME"),
        "store_location": state.get("location", {}).get("store_id")
    }
    
    result = FulfillmentAgent.process_order(order_input)
    
    return {
        "order_status": result,
        "last_worker": "fulfilment_agent",
        "agent_call_history": state["agent_call_history"] + ["fulfilment_agent"],
        "last_error": None if result.get("success") else {
            "code": "FULFILMENT_FAILED",
            "message": result.get("message"),
            "worker": "fulfilment_agent",
            "retryable": True
        }
    }
```

### 4. `nodes/post_purchase.py`

```python
from agents.post_purchase_agent import PostPurchaseAgent
from bson import ObjectId

def post_purchase_agent_node(state):
    input_json = {
        "order_id": state["loyalty_data"]["order_id"],
        "transaction_id": state["payment_status"]["transaction_id"],
        "user_id": state["user_id"],
        "cart_items": state["cart_items"],
        "final_amount": state["loyalty_data"]["final_amount"],
        "delivery_address": state.get("delivery_address", {})
    }
    
    result = PostPurchaseAgent.handle_post_purchase(input_json)
    
    return {
        "order_status": {**state.get("order_status", {}), **result},
        "last_worker": "post_purchase_agent",
        "agent_call_history": state["agent_call_history"] + ["post_purchase_agent"],
        "last_error": None if result.get("success") else {
            "code": "POST_PURCHASE_FAILED",
            "message": result.get("message"),
            "worker": "post_purchase_agent",
            "retryable": False
        }
    }
```

---

## 🔧 Installation

### 1. Install LangGraph

```bash
pip install langgraph langchain-openai
```

### 2. Set Environment Variables

```bash
export OPENAI_API_KEY="your-key-here"  # If using LLM-based intent detector
```

### 3. File Locations

Place all the files in your project:

```
backend/
├── sales_graph/
│   ├── __init__.py
│   ├── state.py
│   ├── graph.py
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── intent_detector.py
│   │   ├── sales_planner.py
│   │   ├── recommend.py
│   │   ├── inventory.py
│   │   ├── loyalty_offers.py      # You need to create this
│   │   ├── payment.py              # You need to create this
│   │   ├── fulfilment.py           # You need to create this
│   │   ├── post_purchase.py        # You need to create this
│   │   └── response_generator.py
```

---

## 🚀 Usage

### Option 1: Direct Python Usage

```python
from sales_graph.graph import run_sales_graph

result = run_sales_graph(
    user_id="507f1f77bcf86cd799439011",  # MongoDB ObjectId as string
    session_id="507f1f77bcf86cd799439012",
    channel="web",
    message="Show me blue kurtis under 2000"
)

print(result["response"])
# Output: {
#   "message": "I found 5 products for you:",
#   "data": {"recommendations": [...]},
#   "prompt": "Would you like to add any to your cart?"
# }
```

### Option 2: FastAPI Integration (Recommended)

Create `routes/sales_graph_routes.py`:

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sales_graph.graph import run_sales_graph
from bson import ObjectId

router = APIRouter(prefix="/chat", tags=["Sales Graph"])

class ChatRequest(BaseModel):
    user_id: str
    session_id: str = None
    channel: str = "web"
    message: str

@router.post("")
async def chat(request: ChatRequest):
    """
    Main conversational endpoint powered by LangGraph.
    """
    try:
        # Generate session_id if not provided
        session_id = request.session_id or str(ObjectId())
        
        result = run_sales_graph(
            user_id=request.user_id,
            session_id=session_id,
            channel=request.channel,
            message=request.message
        )
        
        return {
            "session_id": session_id,
            "response": result.get("response"),
            "debug": {
                "intent": result.get("current_intent"),
                "agents_called": result.get("agent_call_history")
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

Then in `main.py`:

```python
from routes.sales_graph_routes import router as sales_graph_router

app.include_router(sales_graph_router)
```

---

## 🧪 Testing the Flow

### Test 1: Discovery Flow

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "507f1f77bcf86cd799439011",
    "channel": "web",
    "message": "Show me blue kurtis"
  }'
```

**Expected flow:**
```
intent_detector → sales_planner → recommendation_agent → sales_planner → inventory_agent (silent chain) → sales_planner → response_generator
```

### Test 2: Checkout Flow

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "507f1f77bcf86cd799439011",
    "session_id": "existing-session-id",
    "channel": "web",
    "message": "I want to checkout"
  }'
```

**Expected flow:**
```
intent_detector → sales_planner → inventory_agent (silent verify) → sales_planner → loyalty_offers_agent (silent apply offers) → sales_planner → response_generator (order summary gate)
```

---

## 🐛 Debugging Tips

### 1. Enable LangGraph Tracing

```python
from langgraph.graph import StateGraph

# In graph.py, add debug=True
compiled_graph = graph.compile(checkpointer=checkpointer, debug=True)
```

### 2. Inspect State at Each Node

Add logging to any node:

```python
def recommendation_agent_node(state):
    print(f"DEBUG: Entering recommendation_agent")
    print(f"User ID: {state['user_id']}")
    print(f"Intent entities: {state['intent_entities']}")
    # ... rest of code
```

### 3. Check Checkpoint Store

```python
from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = SqliteSaver.from_conn_string("checkpoints.db")

# List all checkpoints
import sqlite3
conn = sqlite3.connect("checkpoints.db")
cursor = conn.execute("SELECT * FROM checkpoints")
print(cursor.fetchall())
```

---

## 🎯 Next Steps

1. **Create the 4 missing worker nodes** (loyalty, payment, fulfilment, post_purchase) using the templates above
2. **Uncomment the node registrations** in `graph.py`
3. **Test the full checkout flow** end-to-end
4. **Add your MongoDB customer profile loading** in a new node or in the sales_planner
5. **Upgrade intent detector to LLM** for better accuracy (see commented code in `intent_detector.py`)

---

## 📚 Reference

- **Design Doc:** `DesignDocByClaude.md` — Full specification
- **LangGraph Docs:** https://langchain-ai.github.io/langgraph/
- **Your Existing Agents:** `agents/` folder

---

## 💡 Key Design Decisions

| Decision | Rationale |
|---|---|
| Rule-based intent detector | Fast, cheap, deterministic for MVP. Can upgrade to LLM later. |
| Template-based responses | Faster than LLM, cheaper. User gets structured JSON anyway. |
| SQLite checkpointer | Easy for local dev. Switch to PostgresSaver for production. |
| Separate worker wrappers | Keeps existing agents unchanged. Easy to test in isolation. |
| Silent chaining limit of 3 | Prevents runaway loops, keeps latency reasonable. |

---

**Questions? Issues?** Check the design doc first, then refer to your existing agent implementations in `agents/`.
