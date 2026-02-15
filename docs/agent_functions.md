# Agent Functions

This document describes the responsibilities and workflows of the core agents currently implemented in the system.

---

## 1. Recommendation Agent

### Purpose
The Recommendation Agent suggests relevant products to users based on their preferences, behavior, and product metadata.

### Inputs
- User profile (from `users` collection)
- Product catalog (from `products` collection)
- Optional context such as search queries or browsing history

### Core Responsibilities
- Analyze user interests and historical interactions
- Match user preferences with product attributes
- Rank products based on relevance
- Return a curated list of recommended products

### Output
A list of recommended products with relevant metadata such as:
- Product ID
- Name
- Category
- Relevance score (optional)

### High-Level Flow
1. Fetch user data from the database.
2. Extract preference signals (categories, brands, price range, etc.).
3. Retrieve matching products from the catalog.
4. Score and rank products.
5. Return top-N recommendations.

---

## 2. Inventory Agent

### Purpose
The Inventory Agent manages product stock information and validates product availability during operations such as ordering or querying.

### Inputs
- Product ID or list of product IDs
- Inventory collection (`inventory` schema)

### Core Responsibilities
- Check current stock levels
- Update inventory after transactions
- Validate availability before confirming an order
- Provide real-time stock status

### Output
Structured inventory status, including:
- Product ID
- Available quantity
- Stock status (In Stock / Low Stock / Out of Stock)

### High-Level Flow
1. Receive request with product identifier(s).
2. Query the inventory collection.
3. Verify stock levels.
4. Return availability status or update quantities if required.

> Note: The Inventory Agent strictly handles stock validation and updates. It does not perform product recommendations or alternative suggestions.

---

