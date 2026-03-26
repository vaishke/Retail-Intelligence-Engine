# Agent Orchestration Design
## Retail Conversational AI System — Multi-Agent LangGraph Architecture

**Version:** 1.0  
**Status:** Engineering Specification  
**Scope:** Sales Planner + 6 Worker Agents, cross-channel, LangGraph implementation

---

## Table of Contents

1. [Overview](#1-overview)
2. [Core Principles](#2-core-principles)
3. [System Agents](#3-system-agents)
4. [Agent Responsibilities and I/O Contracts](#4-agent-responsibilities-and-io-contracts)
5. [Session State Schema](#5-session-state-schema)
6. [Graph Specification](#6-graph-specification)
7. [Orchestration Loop](#7-orchestration-loop)
8. [Planner Policy — Routing and Decision Logic](#8-planner-policy--routing-and-decision-logic)
9. [Silent vs Consent-Gated Transitions](#9-silent-vs-consent-gated-transitions)
10. [Multi-Channel Continuity](#10-multi-channel-continuity)
11. [Error Handling](#11-error-handling)
12. [Payment Idempotency](#12-payment-idempotency)
13. [Session TTL and Stale Data Strategy](#13-session-ttl-and-stale-data-strategy)
14. [LangGraph Checkpoint Strategy](#14-langgraph-checkpoint-strategy)
15. [Extensibility](#15-extensibility)
16. [Limitations and Mitigations](#16-limitations-and-mitigations)

---

## 1. Overview

This document is the **engineering specification** for orchestrating a multi-agent retail conversational AI system. It covers node definitions, edge conditions, state schema, routing policy, error handling, idempotency, and cross-channel continuity.

The system enables a customer to start a conversation on one channel (mobile app, web, WhatsApp) and continue it on another (in-store kiosk, voice) without losing context. A single Sales Planner agent coordinates all specialist Worker Agents in a turn-based, stateful loop.

**End-to-end journey:**
```
Recommendation → Inventory Check → Loyalty/Offers → Payment → Fulfilment → Post-Purchase
```

All stages are orchestrated by the Sales Planner. No worker decides what happens next.

---

## 2. Core Principles

| Principle | Description |
|---|---|
| **Single brain** | Only the Sales Planner has conditional routing edges. Workers never decide flow. |
| **Stateless workers** | Workers read state, execute domain logic, write structured output, return to planner. |
| **State-driven behavior** | `intent + state = next_action`. Same intent with different state can produce different actions. |
| **Silent transitions** | Low-risk background operations chain automatically without interrupting the user. |
| **Consent-gated transitions** | Irreversible actions (payment, reservation) require explicit user confirmation before proceeding. |
| **Turn-based loop** | Each user message triggers exactly one orchestration cycle. The graph waits for user input between turns. |
| **Idempotency on payment** | The payment agent must be safe to call multiple times without double-charging. |

---

## 3. System Agents

| Agent | Role | Type |
|---|---|---|
| `intent_detector` | Classifies user intent from latest message | Processing node |
| `sales_planner` | Central orchestrator — reads intent + state, sets next_action | Decision node (LLM) |
| `recommendation_agent` | Product discovery, bundles, personalised suggestions | Worker node (Tools) |
| `inventory_agent` | Real-time stock check across online and physical stores | Worker node (Tools) |
| `loyalty_offers_agent` | Applies points, coupons, calculates final price with savings | Worker node (Tools) |
| `payment_agent` | Processes payment via saved cards, UPI, gift cards, POS | Worker node (Tools) |
| `fulfilment_agent` | Schedules delivery, reserve-in-store slots, notifies logistics | Worker node (Tools) |
| `post_purchase_agent` | Order tracking, returns, exchanges, feedback | Worker node (Tools) |
| `response_generator` | Formats and sends final user-facing reply | Output node |

---

## 4. Agent Responsibilities and I/O Contracts

Each worker agent has a strict contract defining what it reads from state, what it writes, and what error signals it can return to the planner. Workers never write to fields outside their contract.

---

### 4.1 Sales Planner

**Responsibilities:**
- Run intent detection output through planner policy
- Read full session state (cart, channel, profile, reservation, loyalty, order history)
- Set `next_action` (which worker to call next, or `respond`)
- Set `await_confirmation` flag
- Set `confirmation_context` for templating the consent message
- Never speak to the user directly — delegate all user-facing output to `response_generator`

**Does NOT:**
- Call any external API
- Write domain data to state (that is workers' job)
- Generate user-facing text

---

### 4.2 Intent Detector

**Responsibilities:**
- Classify the latest user message into one of the defined intents
- Update `current_intent` in state
- Optionally extract entities (product name, location, order ID) into `intent_entities`

**READS:** `latest_user_message`, `conversation_summary`

**WRITES:**
```
current_intent: string         # see intent taxonomy in §8
intent_entities: {
  product_query: string | null,
  location: { lat, lng } | null,
  order_id: string | null,
  sku_list: [string] | null
}
```

**Note:** Intent detector is a **separate node** from the Sales Planner. It is a lightweight call (rule-based or small LLM call). Keeping it separate makes the planner's input deterministic and makes intent detection independently testable.

---

### 4.3 Recommendation Agent

**Responsibilities:**
- Analyse customer profile, browsing history, purchase history, seasonal trends
- Query product catalogue API
- Return ranked product list with optional bundle suggestions and active promotions

**READS:** `customer_profile`, `cart_items`, `intent_entities.product_query`, `channel`, `loyalty_data.tier`

**WRITES:**
```
recommended_items: [
  {
    sku: string,
    name: string,
    category: string,
    price: float,
    discounted_price: float | null,
    promotion_tag: string | null,
    image_url: string,
    attributes: { color, size, material, ... }
  }
]
```

**ERRORS:**
```
{ code: "NO_RESULTS", query: string, suggestion: "broaden_filters" }
{ code: "CATALOGUE_API_UNAVAILABLE", retry: true }
```

---

### 4.4 Inventory Agent

**Responsibilities:**
- Check real-time stock for items in cart or recommended items
- Return online availability and nearby store availability with distances
- Offer fulfilment mode options: ship-to-home, click-and-collect, in-store availability

**READS:** `cart_items`, `recommended_items`, `location`, `intent_entities.location`

**WRITES:**
```
inventory_status: {
  [sku]: {
    available_online: bool,
    qty_online: int,
    stores: [
      {
        store_id: string,
        name: string,
        address: string,
        qty: int,
        distance_km: float,
        fulfilment_modes: ["in_store", "click_collect", "ship_from_store"]
      }
    ],
    checked_at: ISO8601_timestamp   # used for TTL validation
  }
}
inventory_verified: bool            # set true when all cart items are confirmed available
```

**ERRORS:**
```
{ code: "ITEM_UNAVAILABLE", sku: string, suggestion: "recommend_similar" }
{ code: "INVENTORY_API_TIMEOUT", retry: true }
```

---

### 4.5 Loyalty and Offers Agent

**Responsibilities:**
- Fetch active promotions applicable to current cart
- Apply loyalty points redemption if customer opts in
- Validate coupon codes
- Calculate final line-item pricing with all discounts
- Show total savings

**READS:** `cart_items`, `customer_profile.loyalty_tier`, `customer_profile.points_balance`, `current_intent`

**WRITES:**
```
loyalty_data: {
  tier: string,
  points_balance: int,
  points_to_redeem: int | null,
  applied_coupons: [string],
  applied_promotions: [{ promo_id, description, discount_value }],
  line_items: [{ sku, original_price, final_price, savings }],
  total_original: float,
  total_final: float,
  total_savings: float,
  calculated_at: ISO8601_timestamp
}
```

**ERRORS:**
```
{ code: "COUPON_INVALID", coupon_code: string }
{ code: "COUPON_EXPIRED", coupon_code: string }
{ code: "PROMOTIONS_SERVICE_UNAVAILABLE", retry: true }
```

---

### 4.6 Payment Agent

**Responsibilities:**
- Process payment using customer's chosen method (saved card, UPI, gift card, in-store POS)
- Handle auth, capture, and failure scenarios
- Use idempotency key to prevent double-charging (see §12)
- Record payment result in state

**READS:** `cart_items`, `loyalty_data.total_final`, `customer_profile.payment_methods`, `payment_idempotency_key`, `retry_count`

**WRITES:**
```
payment_status: {
  status: "pending" | "authorised" | "captured" | "failed" | "declined",
  transaction_id: string | null,
  method_used: string,
  amount_charged: float,
  failure_reason: string | null,
  attempted_at: ISO8601_timestamp
}
```

**ERRORS:**
```
{ code: "PAYMENT_DECLINED", reason: string, retry_allowed: bool }
{ code: "PAYMENT_GATEWAY_TIMEOUT", retry: true }
{ code: "INSUFFICIENT_FUNDS", retry: false }
```

---

### 4.7 Fulfilment Agent

**Responsibilities:**
- Schedule delivery or reserve in-store slot based on customer preference and inventory data
- Notify logistics system or store staff
- Generate order confirmation with fulfilment details

**READS:** `cart_items`, `inventory_status`, `payment_status`, `customer_profile.address`, `location`, `reservation_status`

**WRITES:**
```
reservation_status: {
  reserved: bool,
  store_id: string | null,
  slot: ISO8601_timestamp | null,
  reservation_id: string | null,
  expires_at: ISO8601_timestamp | null   # reservation TTL
}
order_status: {
  order_id: string,
  fulfilment_mode: "delivery" | "click_collect" | "in_store_pickup",
  estimated_delivery: ISO8601_timestamp | null,
  tracking_url: string | null,
  confirmed_at: ISO8601_timestamp
}
```

**ERRORS:**
```
{ code: "SLOT_UNAVAILABLE", suggestion: "offer_alternatives" }
{ code: "LOGISTICS_API_UNAVAILABLE", retry: true }
```

---

### 4.8 Post Purchase Agent

**Responsibilities:**
- Track shipment status for delivered orders
- Handle return and exchange requests
- Solicit and record post-purchase feedback
- Apply loyalty points earned from the purchase

**READS:** `order_status`, `customer_profile`, `intent_entities.order_id`

**WRITES:**
```
order_status: {
  ...existing fields,
  tracking_status: string,
  tracking_events: [{ timestamp, description, location }],
  return_request: { initiated: bool, reason: string | null, status: string } | null,
  feedback: { rating: int | null, comment: string | null, submitted_at: ISO8601_timestamp | null }
}
customer_profile.points_balance: int   # updated after purchase earn
```

---

## 5. Session State Schema

This is the complete state object that persists across all channels and all turns within a session.

```python
class SessionState(TypedDict):
    # ── Identity ────────────────────────────────────────────────────
    user_id: str
    session_id: str                     # unique per conversation thread
    channel: str                        # "web" | "mobile" | "kiosk" | "whatsapp" | "telegram" | "voice"
    channel_history: list[str]          # all channels this session has touched
    location: dict | None               # { lat, lng, store_id? }

    # ── Customer Context ────────────────────────────────────────────
    customer_profile: dict              # demographics, purchase history, loyalty tier, saved payment methods
    conversation_summary: str           # running LLM-generated summary for context compression

    # ── Cart and Products ───────────────────────────────────────────
    cart_items: list[dict]              # [{ sku, name, qty, price }]
    recommended_items: list[dict]       # output of recommendation_agent
    inventory_status: dict              # output of inventory_agent, keyed by sku
    inventory_verified: bool            # true if all cart items confirmed available
    inventory_checked_at: str | None    # ISO8601, used for TTL validation

    # ── Offers and Pricing ──────────────────────────────────────────
    loyalty_data: dict | None           # output of loyalty_offers_agent

    # ── Fulfilment ──────────────────────────────────────────────────
    reservation_status: dict | None     # output of fulfilment_agent (pre-payment)
    order_status: dict | None           # output of fulfilment_agent (post-payment)

    # ── Payment ─────────────────────────────────────────────────────
    payment_status: dict | None         # output of payment_agent
    payment_idempotency_key: str | None # see §12, generated once per cart state

    # ── Orchestration Control ───────────────────────────────────────
    current_intent: str                 # latest classified intent
    intent_entities: dict               # extracted entities from latest message
    next_action: str                    # which worker to call, or "respond"
    await_confirmation: bool            # if True, surface response and halt chaining
    confirmation_context: str | None    # what we are asking the user to confirm
    agent_call_history: list[str]       # ordered list of agents called this session
    last_worker: str | None             # last worker agent that ran
    retry_count: dict                   # { worker_name: int } — per-worker retry tracker

    # ── Stale Data Flags ────────────────────────────────────────────
    stale_flags: dict                   # { "inventory": bool, "loyalty": bool, ... }
```

---

## 6. Graph Specification

### 6.1 Node Definitions

| Node | Type | Description |
|---|---|---|
| `START` | Entry | LangGraph built-in entry point |
| `intent_detector` | Processing | Classifies intent, extracts entities, updates state |
| `sales_planner` | Decision (LLM) | Reads intent + state, sets next_action and await_confirmation |
| `recommendation_agent` | Worker (Tools) | Product discovery and ranking |
| `inventory_agent` | Worker (Tools) | Real-time stock check |
| `loyalty_offers_agent` | Worker (Tools) | Offer application and pricing |
| `payment_agent` | Worker (Tools) | Payment processing |
| `fulfilment_agent` | Worker (Tools) | Delivery/reservation scheduling |
| `post_purchase_agent` | Worker (Tools) | Tracking, returns, feedback |
| `response_generator` | Output | Formats and emits user-facing message |
| `END` | Exit | LangGraph built-in exit point |

### 6.2 Edge Definitions

| From | To | Condition |
|---|---|---|
| `START` | `intent_detector` | Always |
| `intent_detector` | `sales_planner` | Always |
| `sales_planner` | `recommendation_agent` | `next_action == "recommendation_agent"` |
| `sales_planner` | `inventory_agent` | `next_action == "inventory_agent"` |
| `sales_planner` | `loyalty_offers_agent` | `next_action == "loyalty_offers_agent"` |
| `sales_planner` | `payment_agent` | `next_action == "payment_agent"` |
| `sales_planner` | `fulfilment_agent` | `next_action == "fulfilment_agent"` |
| `sales_planner` | `post_purchase_agent` | `next_action == "post_purchase_agent"` |
| `sales_planner` | `response_generator` | `next_action == "respond"` OR `await_confirmation == True` |
| `recommendation_agent` | `sales_planner` | Always |
| `inventory_agent` | `sales_planner` | Always |
| `loyalty_offers_agent` | `sales_planner` | Always |
| `payment_agent` | `sales_planner` | Always |
| `fulfilment_agent` | `sales_planner` | Always |
| `post_purchase_agent` | `sales_planner` | Always |
| `response_generator` | `END` | Always |

### 6.3 Topology Diagram

```
START
  │
  ▼
intent_detector
  │
  ▼
sales_planner ◄──────────────────────────────────────────────┐
  │                                                           │
  ├──► recommendation_agent ──────────────────────────────── ┤
  │                                                           │
  ├──► inventory_agent ───────────────────────────────────── ┤
  │                                                           │
  ├──► loyalty_offers_agent ──────────────────────────────── ┤
  │                                                           │
  ├──► payment_agent ─────────────────────────────────────── ┤
  │                                                           │
  ├──► fulfilment_agent ──────────────────────────────────── ┘
  │
  ├──► post_purchase_agent ──► sales_planner (loop back)
  │
  └──► response_generator
            │
           END
```

**Key rules enforced by topology:**
- Only `sales_planner` has conditional outgoing edges
- Every worker has exactly one outgoing edge: back to `sales_planner`
- No worker-to-worker edges exist
- Only `response_generator` connects to `END`
- `sales_planner` never connects to `END` directly

---

## 7. Orchestration Loop

### 7.1 Per-Turn Execution Flow

```
1. User sends message
2. Session state is loaded from checkpoint store (keyed by session_id)
3. Graph enters at START → intent_detector
4. intent_detector classifies intent, writes current_intent + intent_entities
5. sales_planner reads intent + full state
6. sales_planner sets next_action + await_confirmation
7. If await_confirmation == True → route to response_generator → END turn
8. Else → route to next worker agent
9. Worker executes, updates state, returns to sales_planner
10. sales_planner re-evaluates: more silent chaining needed?
    - If yes → set next_action to next worker, await_confirmation = False → repeat from step 8
    - If no  → set next_action = "respond" → route to response_generator → END turn
11. State checkpoint saved
12. Wait for next user message
```

### 7.2 Loop Termination Conditions

The loop for a given turn ends when any of the following is true:

- `await_confirmation == True` — system must surface a message and wait for user
- `next_action == "respond"` — planner has determined all required work is done
- A worker returns an unrecoverable error and planner sets `next_action = "respond"` with an apology directive
- `agent_call_history` for the current turn exceeds the safety limit of **5 worker calls** (prevents runaway loops)

### 7.3 Session End Conditions

A session is considered complete when:

- `order_status.confirmed_at` is set (purchase completed), OR
- User explicitly ends session, OR
- Session exceeds inactivity TTL (see §13)

---

## 8. Planner Policy — Routing and Decision Logic

### 8.1 Intent Taxonomy

| Intent | Description | Example Trigger |
|---|---|---|
| `discovery` | User wants product suggestions | "Show me blue kurtis" |
| `refine_recommendations` | User wants to filter or modify suggestions | "Show more under ₹1000" |
| `availability_check` | User wants to know if items are in stock | "Are these available near me?" |
| `reservation_request` | User wants to reserve items in-store | "Can you hold these for me?" |
| `offer_inquiry` | User asks about discounts or loyalty points | "Do I have any offers?" |
| `checkout_intent` | User wants to initiate payment | "I want to buy these" |
| `checkout_confirmation` | User confirms they want to proceed after seeing summary | "Yes, confirm" |
| `payment_method_selection` | User selects or changes payment method | "Use my UPI" |
| `order_tracking` | User wants to know status of a past order | "Where is my order?" |
| `return_request` | User wants to return or exchange | "I want to return this" |
| `general_query` | Out-of-scope or clarification needed | "What are your store hours?" |

### 8.2 Routing Policy (Pseudocode)

```python
def planner_policy(intent: str, state: SessionState) -> tuple[str, bool, str | None]:
    """
    Returns: (next_action, await_confirmation, confirmation_context)
    """

    # ── Discovery ───────────────────────────────────────────────────
    if intent == "discovery" or intent == "refine_recommendations":
        return "recommendation_agent", False, None

    # After recommendation returns, planner auto-chains to inventory
    # This is a silent chain — handled in post-worker evaluation (§8.3)

    # ── Availability ────────────────────────────────────────────────
    if intent == "availability_check":
        if not state.cart_items and not state.recommended_items:
            return "respond", False, None   # tell user to select items first
        return "inventory_agent", False, None

    # ── Reservation ─────────────────────────────────────────────────
    if intent == "reservation_request":
        if not state.inventory_verified:
            return "inventory_agent", False, None   # verify first, silently
        # inventory verified — gate on user confirmation
        return "respond", True, "reservation_summary"

    # ── Offers ──────────────────────────────────────────────────────
    if intent == "offer_inquiry":
        return "loyalty_offers_agent", False, None

    # ── Checkout ────────────────────────────────────────────────────
    if intent == "checkout_intent":
        if not state.cart_items:
            return "respond", False, None   # empty cart message

        if not state.inventory_verified or is_stale(state, "inventory"):
            return "inventory_agent", False, None   # silent re-verify

        if not state.loyalty_data or is_stale(state, "loyalty"):
            return "loyalty_offers_agent", False, None   # silent apply offers

        # all preconditions met — show order summary and gate
        return "respond", True, "order_summary"

    if intent == "checkout_confirmation":
        return "payment_agent", False, None

    # ── Post-Payment Silent Chain ────────────────────────────────────
    # Handled in post-worker evaluation (§8.3)

    # ── Post Purchase ───────────────────────────────────────────────
    if intent == "order_tracking" or intent == "return_request":
        return "post_purchase_agent", False, None

    # ── Fallback ────────────────────────────────────────────────────
    return "respond", False, None
```

### 8.3 Post-Worker Silent Chaining Rules

After a worker completes, the planner re-evaluates state before deciding to respond or chain. These are the defined silent chaining rules:

| Worker Just Ran | State Condition | Auto-Chain To |
|---|---|---|
| `recommendation_agent` | `intent == "discovery"` and `cart_items` has new items | `inventory_agent` |
| `inventory_agent` | `intent == "checkout_intent"` and `inventory_verified == True` and no loyalty_data | `loyalty_offers_agent` |
| `payment_agent` | `payment_status.status == "captured"` | `fulfilment_agent` |
| `inventory_agent` | `ITEM_UNAVAILABLE` error returned | `recommendation_agent` (suggest alternatives) |
| Any worker | `retry_count[worker] < MAX_RETRIES` and retryable error | Same worker again |

### 8.4 Multi-Intent Handling

When a user message contains multiple intents (e.g., "Are my cart items available and do I have any offers?"), the planner applies **priority ordering**:

1. **Critical/in-progress action** — if a payment or reservation confirmation is pending, always handle that first
2. **Transactional intents** — checkout, reservation, payment take priority over discovery
3. **Sequential silent resolution** — for genuinely parallel intents of equal priority (availability + offers), execute workers in sequence silently, respond once with combined output
4. **Single response per turn** — the user always receives one coherent message, not two separate responses

---

## 9. Silent vs Consent-Gated Transitions

### 9.1 Silent Transitions

Workers chain automatically. User is not interrupted. Used for low-risk background operations.

| Trigger | Silent Chain |
|---|---|
| Recommendations returned | Auto-check inventory for recommended items |
| Checkout intent detected | Auto-apply loyalty offers before showing order summary |
| Payment captured | Auto-trigger fulfilment scheduling |
| Inventory miss on cart item | Auto-fetch similar recommendations |
| Pre-checkout with stale inventory data | Auto-revalidate stock before gating |

**Implementation:** `await_confirmation = False` and `next_action = <worker_name>` in planner output.

### 9.2 Consent-Gated Transitions

Planner halts worker chaining, surfaces a message to user, and waits for explicit confirmation.

| Gate Point | What User Must Confirm |
|---|---|
| Before reservation | Store name, slot, items being held |
| Before payment | Full order summary: items, final price, savings, payment method |
| Before payment method change | "Are you sure you want to switch from saved card to UPI?" |
| Before return initiation | Item, reason, return method |

**Implementation:** `await_confirmation = True` and `confirmation_context = <template_key>` in planner output. The `response_generator` uses `confirmation_context` to select the correct message template.

---

## 10. Multi-Channel Continuity

### 10.1 How Channel Switching Works

Channel switching is a **state persistence problem**, not a graph problem. The graph topology stays identical across all channels. Only the session state is reloaded.

```
Mobile App (turn 1–5)
  └── State checkpoint saved after each turn

In-Store Kiosk login
  └── User authenticates → session_id resolved from user_id
  └── State loaded from checkpoint store
  └── Graph enters at START → intent_detector with full prior state
  └── Conversation continues from where it left off
```

### 10.2 Channel-Specific Behaviour

| Channel | Notes |
|---|---|
| `web` / `mobile` | Full rich UI — show product images, price cards, CTAs |
| `whatsapp` / `telegram` | Text-based — use condensed text responses, no image embeds |
| `kiosk` | Large screen, touch — show expanded product cards, barcode scan support |
| `voice` | Text-to-speech friendly — strip markdown, use natural sentence structure |

The `response_generator` node reads `state.channel` to format output appropriately. The planner and workers are channel-agnostic.

### 10.3 Session Security on Channel Switch

When a session is resumed on a new channel:

- Reject checkpoints older than **4 hours** for kiosk (physical security risk)
- Require re-authentication (PIN or loyalty card scan) on kiosk channel switch
- Log the channel switch event to `channel_history`

---

## 11. Error Handling

### 11.1 Worker Failure Handling Matrix

| Scenario | Retry? | Max Retries | Planner Action After Max |
|---|---|---|---|
| API timeout (any worker) | Yes | 2 | Apologise, offer to retry manually |
| Inventory unavailable for cart item | No | — | Route to recommendation_agent for alternatives |
| Payment declined | Yes | 2 | Ask user to try different payment method |
| Payment gateway timeout | Yes | 2 | Hold state, show "processing" status, retry |
| Coupon invalid/expired | No | — | Remove coupon from state, recalculate, inform user |
| Slot unavailable for reservation | No | — | Offer next available slot or ship-to-home |
| Logistics API unavailable | Yes | 2 | Inform user of delay, trigger manual follow-up flag |

### 11.2 Retry Mechanics

Retry count is tracked per worker in `state.retry_count[worker_name]`. The planner checks this before routing:

```python
if state.retry_count.get(worker_name, 0) >= MAX_RETRIES[worker_name]:
    # do not retry — route to response_generator with error directive
    return "respond", False, None
```

**Max retries per worker:**

| Worker | Max Retries |
|---|---|
| `recommendation_agent` | 1 |
| `inventory_agent` | 2 |
| `loyalty_offers_agent` | 1 |
| `payment_agent` | 2 |
| `fulfilment_agent` | 2 |
| `post_purchase_agent` | 1 |

### 11.3 Payment Failure Flow

```
payment_agent returns PAYMENT_DECLINED
  └── planner checks retry_count["payment_agent"]
      ├── < 2: increment counter, set await_confirmation = True
      │          confirmation_context = "payment_retry"
      │          (ask user to retry or try different method)
      └── >= 2: set await_confirmation = True
                confirmation_context = "payment_failed_final"
                (offer alternative: different card / UPI / COD)
                reservation_status remains intact for X minutes
```

### 11.4 Reservation on Payment Failure

If payment ultimately fails after all retries, the reservation is **not immediately released**. The planner sets a grace period flag (`reservation_grace_until = now + 30 minutes`). If the user retries payment within this window, the reservation remains valid. After the grace period, the fulfilment agent is called silently to release the slot.

---

## 12. Payment Idempotency

This section is non-negotiable for production. If the payment node is called more than once (due to retry logic, graph re-entry, or a crash mid-execution), the customer must never be charged twice.

### 12.1 Idempotency Key Generation

An idempotency key is generated **once** when the user first confirms checkout intent. It is stored in `state.payment_idempotency_key` and passed to the payment gateway on every payment attempt.

```python
def generate_idempotency_key(state: SessionState) -> str:
    cart_hash = hashlib.sha256(
        json.dumps(state.cart_items, sort_keys=True).encode()
    ).hexdigest()[:16]
    return f"{state.session_id}_{cart_hash}"
```

### 12.2 Key Lifecycle Rules

- The key is generated **once** when `checkout_confirmation` intent is first processed
- The same key is reused on all payment retries for the same cart
- The key is **invalidated and regenerated** only if `cart_items` changes (different items = different transaction)
- The payment gateway uses this key to deduplicate: if a transaction with this key already succeeded, it returns the existing success result without charging again
- The key is never regenerated simply because a retry is happening

### 12.3 Implementation in Planner

```python
# Before routing to payment_agent:
if not state.payment_idempotency_key:
    state.payment_idempotency_key = generate_idempotency_key(state)
# Do NOT regenerate key on retry if cart hasn't changed
```

---

## 13. Session TTL and Stale Data Strategy

Data fetched mid-session has a finite validity window. Checking inventory at 10am does not guarantee stock at 3pm, especially for in-store reservations.

### 13.1 TTL Definitions

| Data Type | TTL | State Field |
|---|---|---|
| Inventory status | 15 minutes | `inventory_checked_at` |
| Loyalty/offers data | 30 minutes | `loyalty_data.calculated_at` |
| Recommendations | 60 minutes | Implicit (profile-driven, not time-critical) |
| Reservation slot | Until `reservation_status.expires_at` (set by store, typically 2–4 hours) |
| Session inactivity | 4 hours (kiosk), 24 hours (mobile/web) | — |

### 13.2 Stale Data Check (Used Pre-Checkout)

```python
def is_stale(state: SessionState, data_type: str) -> bool:
    TTL = {
        "inventory": timedelta(minutes=15),
        "loyalty": timedelta(minutes=30)
    }
    checked_at_field = {
        "inventory": state.inventory_checked_at,
        "loyalty": state.loyalty_data.get("calculated_at") if state.loyalty_data else None
    }
    checked_at = checked_at_field.get(data_type)
    if not checked_at:
        return True
    return datetime.utcnow() - datetime.fromisoformat(checked_at) > TTL[data_type]
```

The planner calls `is_stale()` before routing to payment. If inventory or loyalty data is stale, it silently re-validates both before showing the order summary gate.

### 13.3 Reservation Expiry Handling

If the user returns to a session after a long gap and the reservation has expired (`reservation_status.expires_at < now`):

1. Planner detects expired reservation on session load
2. Silently calls `inventory_agent` to re-check availability
3. If still available, silently calls `fulfilment_agent` to re-reserve
4. If unavailable, informs user and routes to `recommendation_agent` for alternatives

---

## 14. LangGraph Checkpoint Strategy

### 14.1 Checkpoint Store Selection

| Environment | Checkpoint Store | Reason |
|---|---|---|
| Local development | `SqliteSaver` | Zero infrastructure, easy inspection |
| Production | `PostgresSaver` | Durable, concurrent-safe, queryable |

### 14.2 Checkpoint Key

The checkpoint key is a composite of `user_id` and `session_id`:

```
checkpoint_key = f"{user_id}::{session_id}"
```

**Why not just `user_id`?** A single user may have multiple active sessions simultaneously across channels (e.g., browsing on mobile while at kiosk). `session_id` scopes the checkpoint correctly.

### 14.3 Session Resume Logic

```python
def resume_session(user_id: str, channel: str) -> SessionState:
    session_id = resolve_active_session(user_id)   # look up most recent session
    state = load_checkpoint(f"{user_id}::{session_id}")

    # Security check for high-risk channels
    if channel == "kiosk":
        session_age = datetime.utcnow() - state.last_active_at
        if session_age > timedelta(hours=4):
            raise SessionExpiredError("Re-authentication required")

    state.channel = channel
    state.channel_history.append(channel)
    return state
```

### 14.4 Checkpoint Frequency

State is checkpointed **after every node execution**, not just after full turns. This means if the system crashes mid-checkout (after payment succeeded but before fulfilment), the graph can resume exactly where it left off without re-triggering payment.

---

## 15. Extensibility

To add a new worker agent (e.g., a `returns_agent` or `size_advisor_agent`):

1. **Define the agent** — implement its tool functions and I/O contract following the pattern in §4
2. **Update planner policy** — add intent condition(s) and routing logic in §8.2
3. **Add routing entry** — add the new node and its conditional edge from `sales_planner` in the graph definition
4. **Update state schema** — add any new state fields the worker reads/writes

No other nodes need to change. Existing agents are unaffected.

---

## 16. Limitations and Mitigations

| Limitation | Risk | Mitigation |
|---|---|---|
| Planner policy complexity grows over time | Hard to maintain if all logic lives in one function | Modularise policy into intent-specific handlers; write unit tests per intent path |
| Incorrect intent detection causes misrouting | User gets wrong agent, bad experience | Keep intent_detector as a separate testable node; add confidence threshold — low confidence → ask clarification |
| Silent chaining increases turn latency | User waits longer between message and response | Cap silent chain depth at 3 workers per turn; show typing indicators per channel |
| Overuse of LLM in planner for simple decisions | High token cost for deterministic routing | Use rule-based routing for well-defined intents (checkout, tracking); use LLM only for ambiguous or compound intents |
| State consistency under concurrent channel access | Two channels update state simultaneously | Use optimistic locking on checkpoint writes; last-write-wins with conflict detection |
| Stale reservation on payment failure | Customer loses slot | Grace period mechanism in §11.4 handles this; alert store staff for manual hold if grace expires |
| Worker I/O contract drift | Worker updates state shape, planner silently misreads | Define and version state contracts; add schema validation in worker output before state write |

---

*End of Document*
