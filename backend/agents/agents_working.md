# Retail Intelligence Engine – Agents Documentation

## Overview

The `agents/` folder contains modular components that handle the business logic and orchestration for the Retail Intelligence Engine (RIE). Each agent encapsulates a specific domain of functionality, enabling a **single responsibility design** while allowing the `SalesAgent` to orchestrate end-to-end operations.

---

## 1. `RecommendationAgent`

**Purpose:** Provides personalized product recommendations to users based on their preferences, constraints, and past interactions.

**Key Functions:**

* `recommend_products(user_id, constraints, top_k=5, exclude_product_ids=None)`
  Generates a ranked list of recommended products for a user according to category, subcategory, color, tags, and price range. Scores products based on relevance and popularity.

* `_build_query(constraints)`
  Internal method to construct MongoDB query filters from constraints.

* `_score_products(products, constraints)`
  Assigns a score to products based on matching signals (category, subcategory, tags, ratings).

* `_build_reason(signals)`
  Generates a human-readable reason for the recommendation.

* `handle_request(recommendation_request)`
  Entry point for external requests, wraps `recommend_products`.

**Notes:**

* Integrates seamlessly with session context to exclude previously selected products.
* Scoring considers both user constraints and product popularity.

---

## 2. `InventoryAgent`

**Purpose:** Manages product stock information and inventory adjustments across multiple stores.

**Key Functions:**

* `check_stock(product_id, store_id=None)`
  Checks availability of a product across all stores or a specific store. Returns total stock and per-store stock details.

* `deduct_stock(product_id, store_id, quantity)`
  Deducts a given quantity from the inventory, validating stock availability. Updates `last_updated`.

* `get_store_stock(product_id)`
  Retrieves stock quantities for all stores.

* `handle_request(inventory_request)`
  Generic entry point for actions like `"check_stock"`, `"deduct_stock"`, or `"get_store_stock"`.

**Notes:**

* All product references are MongoDB `ObjectId`s.
* Supports multi-store operations, critical for fulfillment logic.

---

## 3. `OfferLoyaltyAgent`

**Purpose:** Handles user loyalty points, coupon application, and order preparation with discounts.

**Key Functions:**

* `process_checkout(user_id, cart_items, coupon_code=None, use_points=0)`
  Calculates final price considering coupon codes and loyalty point redemption. Updates user loyalty points and tier. Inserts the order in the database.

* `apply_coupon(coupon_code, cart_total)`
  Applies active offers and returns the discount amount.

* `earn_points(amount)`
  Calculates loyalty points earned per ₹100 spent.

* `get_user_loyalty_status(user_id)`
  Returns the current tier and points of a user.

* `view_available_offers()`
  Lists all active offers.

**Notes:**

* Supports tier upgrades: Silver → Gold → Platinum.
* Ensures all applied discounts and points are recorded in the order schema.

---

## 4. `FulfillmentAgent`

**Purpose:** Orchestrates inventory reservation and order fulfillment.

**Key Functions:**

* `process_order(order: dict)`
  Processes an order:

  * Deducts inventory using `InventoryAgent`.
  * Determines fulfillment status (`FULFILLED`, `PARTIALLY_FULFILLED`, `FAILED`).
  * Persists the order with fulfillment status in the database.

**Notes:**

* Integrates closely with `InventoryAgent` to ensure availability before finalizing orders.
* Supports multiple fulfillment types and dynamic store selection.

---

## 5. `PaymentAgent`

**Purpose:** Handles order payments and updates order payment status.

**Key Functions:**

* `process_payment(order_id: str, payment_method: str, details: dict = None)`
  Processes payment for an order. Updates the order’s `payment` sub-document. Generates a unique transaction ID.

**Notes:**

* Simulates a payment gateway; can be integrated with external payment services.
* Ensures idempotent payment handling (prevents double payment).

---

## 6. `PostPurchaseAgent`

**Purpose:** Performs post-purchase operations including inventory adjustments, shipment creation, invoice generation, and notifications.

**Key Functions:**

* `confirm_order(order_id, transaction_id)`
  Confirms payment and updates order status.

* `reduce_inventory(delivery_city, cart_items)`
  Updates inventory based on delivery city and order quantities.

* `create_shipment(order_id, user_id, delivery_address, shipment_type, carrier, tracking_number)`
  Generates a shipment record with tracking information.

* `generate_invoice(order_id, cart_items, final_amount)`
  Creates an invoice for the order.

* `send_notification(user_id, order_id)`
  Sends an order confirmation notification to the user.

* `handle_post_purchase(input_json)`
  High-level method to handle all post-purchase steps sequentially.

**Notes:**

* Ensures end-to-end post-order workflow is executed reliably.
* Integrates with `InventoryAgent`, `Shipments`, `Invoices`, and `Notifications`.

---

## 7. `SalesAgent`

**Purpose:** Orchestrates all other agents to manage **end-to-end customer interactions**, from session management to post-purchase completion.

**Key Functions:**

* **Session Handling:**

  * `start_session(user_id, channel)`
  * `get_session(session_id)`
  * `update_session(session_id, updates)`
  * `end_session(session_id)`

* **Recommendations:**

  * `recommend_products(session_id, constraints=None)`

* **Inventory Checks:**

  * `check_inventory(session_id, store_id=None)`

* **Checkout & Fulfillment:**

  * `checkout(session_id, coupon_code=None, use_points=0, store_location=None, fulfillment_type="SHIP_TO_HOME")`
    Integrates `OfferLoyaltyAgent` and `FulfillmentAgent`.

* **Payment:**

  * `process_payment(session_id, payment_method, details=None)`

* **Post-Purchase:**

  * `post_purchase(session_id, delivery_address)`
    Calls `PostPurchaseAgent` for shipment, invoice, and notifications.

**Notes:**

* Acts as the **main orchestrator**, coordinating all worker agents.
* Maintains session context for user interaction tracking and workflow state.
* Handles formatting of cart items and proper ObjectId conversions for downstream agents.

---

## Agent Interaction Flow

1. **SalesAgent** starts a session with a user.
2. **RecommendationAgent** provides product suggestions based on user preferences.
3. **InventoryAgent** checks stock availability for selected products.
4. **OfferLoyaltyAgent** applies discounts and calculates final amount.
5. **FulfillmentAgent** reserves inventory and updates order status.
6. **PaymentAgent** processes the payment for the order.
7. **PostPurchaseAgent** finalizes the order by confirming, shipping, invoicing, and notifying the user.

---

## Summary

* Each agent is **single-responsibility** and interacts with MongoDB collections as per the latest schema.
* `SalesAgent` is the **central coordinator**, ensuring seamless flow between recommendation, checkout, payment, and post-purchase operations.
* Designed for **modularity and maintainability**, allowing future addition of new agents (e.g., MarketingAgent, AnalyticsAgent) without changing the main orchestrator.
