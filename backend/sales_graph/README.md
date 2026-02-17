## Agent Orchestration Design

### 1. Overview

This document defines how the Sales Planner coordinates all Worker Agents in a unified retail conversational system. The orchestration is implemented as a stateful LangGraph loop where the planner is the only decision-making node and all workers are deterministic executors.

Goal: deliver a seamless end-to-end journey across channels — recommendation → inventory → offers → payment → fulfilment → post-purchase — while preserving context and enforcing user consent for critical actions.

---

### 2. Core Principles

* Single brain architecture: only the Sales Planner decides routing.
* Worker agents are stateless executors; they never decide flow.
* State drives behavior; intent + state = next action.
* Silent transitions for cheap/background checks.
* Consent-gated transitions for irreversible operations (e.g., payment).
* Turn-based loop: each user message triggers one orchestration cycle.

---

### 3. Agents in the System

* Sales Planner Agent
* Recommendation Agent
* Inventory Agent
* Loyalty & Offers Agent
* Payment Agent
* Fulfilment Agent
* Post Purchase Agent

---

### 4. Responsibilities

#### 4.1 Sales Planner Agent

Central orchestrator.

* Detects intent from user input
* Reads full session state (cart, history, channel, promotions)
* Decides next_action
* Determines if transition is silent or requires user confirmation
* Generates high-level response directives

It never performs domain tasks directly.

#### 4.2 Worker Agents

Each worker:

* Reads relevant state
* Calls domain tools/APIs
* Writes structured outputs back to state
* Returns control to Sales Planner

They do not speak to the user directly and do not route to other agents.

---

### 5. Graph Topology (High-Level)

START → Intent Detection → Sales Planner → (Conditional Worker) → Sales Planner → Response → END (turn)

All workers always return to Sales Planner. No worker-to-worker edges exist.

---

### 6. Session State Schema (Core Fields)

* user_id
* channel (web, mobile, kiosk, messaging, voice)
* location
* customer_profile
* cart_items
* recommended_items
* inventory_status
* reservation_status
* loyalty_data
* payment_status
* order_status
* conversation_summary
* current_intent
* next_action
* await_confirmation (bool)
* confirmation_context

State persists across channels and sessions.

---

### 7. Orchestration Loop

On each user message:

1. Load session state
2. Detect intent
3. Planner evaluates intent + state
4. Planner sets next_action and await_confirmation flag
5. Route to selected worker OR respond
6. Worker updates state
7. Planner decides if more silent chaining is needed
8. Final response generated
9. End turn and wait for next user input

This loop repeats until purchase completion or session end.

---

### 8. Silent vs Consent-Gated Transitions

#### Silent Transitions

Automatically chain workers without user interruption.
Used for low-risk background tasks.

Examples:

* Recommendation → Inventory check
* Checkout intent → Apply loyalty offers
* Payment success → Trigger fulfilment scheduling

#### Consent-Gated Transitions

Planner must ask user before proceeding.

Examples:

* Initiating payment
* Reserving items in-store
* Confirming final order summary

Controlled via:
await_confirmation = True/False

If True, system responds and halts worker chaining until user confirms.

---

### 9. Routing Logic (Planner Policy)

Routing is based on intent + precondition validation.

Examples:

* Discovery intent → Recommendation Agent
* Availability query → Inventory Agent
* Checkout intent → validate cart → maybe inventory → then payment
* Offer inquiry → Loyalty & Offers Agent
* Reservation request → Fulfilment Agent
* Order tracking → Post Purchase Agent

Preconditions prevent invalid flows (e.g., checkout with empty cart).

---

### 10. Multi-Channel Continuity

All channels share the same session state store.
When a user switches from mobile to kiosk:

* Session state is reloaded
* Graph re-enters at Intent Detection → Planner
* Flow continues without restarting conversation context

This enables seamless cross-channel journeys.

---

### 11. Error Handling Strategy

* Worker failure → planner decides retry, fallback, or apology response
* Payment failure → retry logic + alternative method suggestion
* Inventory mismatch → suggest similar products via Recommendation Agent
* Stale data → planner can trigger silent re-validation before checkout

---

### 12. Extensibility

To add a new worker agent:

1. Define its tool functions
2. Add planner policy condition for new intent/use case
3. Add routing entry in conditional edge map
   No structural graph changes required.

---

### 13. Limitations

* Planner complexity can grow if policy logic is not modularized
* Incorrect intent detection can misroute flows
* Overuse of silent chaining may increase latency
* Requires strict state consistency to avoid incorrect confirmations

---

### 14. Summary

This orchestration design provides a controlled, state-driven multi-agent system where the Sales Planner acts as the central coordinator and worker agents execute domain tasks deterministically. It supports cross-channel continuity, dynamic user intent shifts, and safe progression through commerce flows while maintaining clear separation of concerns and extensibility.
