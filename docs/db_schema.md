# Retail Intelligence Engine – Database Schema

## Users
```json
{
  "_id": "ObjectId",
  "name": "String",
  "email": "String",
  "password_hash": "String",
  "gender": "String",
  "location": "String",
  "preferences": {
    "styles": ["String"],
    "colors": ["String"],
    "price_range": ["Number", "Number"]
  },
  "loyalty": {
    "tier": "String",
    "points": "Number"
  },
  "past_purchases": ["String"],
  "payment_methods": [
    {
      "type": "String",
      "details": "String",
      "expiry_date": "String"
    }
  ],
  "created_at": "Date"
}
```

## Sessions
```json
{
  "_id": "ObjectId",
  "user_id": "String",
  "device": "String",
  "status": "String",
  "channel": "String",
  "chat_history": [
    {
      "role": "String",
      "message": "String",
      "timestamp": "Date"
    }
  ],
  "context": {
    "current_intent": "String",
    "selected_products": ["String"]
  },
  "created_at": "Date"
}
```

## Products

```json
{
  "_id": "ObjectId",
  "name": "String",
  "category": "String",
  "subcategory": "String",
  "price": "Number",
  "description": "String",
  "images": ["String"],
  "attributes": {
    "color": "String",
    "material": "String",
    "size_available": ["String"]
  },
  "ratings": "Number",
  "tags": ["String"],
  "available_stores": [
    {
      "store_id": "String",
      "stock": "Number"
    }
  ],
  "created_at": "Date"
}
```

## Inventory

```json
{
  "_id": "ObjectId",
  "product_id": "String",
  "store_id": "String",
  "quantity": "Number",
  "last_updated": "Date"
}
```

## Orders

```json
{
  "_id": "ObjectId",
  "user_id": "String",
  "session_id": "String",
  "items": [
    {
      "product_id": "String",
      "qty": "Number",
      "price": "Number"
    }
  ],
  "discounts_applied": [
    {
      "type": "String",
      "code": "String",
      "amount": "Number"
    }
  ],
  "final_price": "Number",
  "payment": {
    "status": "String",
    "method": "String",
    "transaction_id": "String"
  },
  "fulfillment": {
    "type": "String",
    "status": "String"
  },
  "created_at": "Date"
}
```

## Offers

```json
{
  "_id": "ObjectId",
  "code": "String",
  "description": "String",
  "discount_percent": "Number",
  "valid_till": "Date",
  "applicable_categories": ["String"],
  "min_purchase_amount": "Number",
  "is_active": "Boolean"
}
```

## Shipments

```json
{
  "_id": "ObjectId",
  "order_id": "String",
  "user_id": "String",
  "shipment_type": "String",
  "carrier": "String",
  "tracking_number": "String",
  "expected_delivery_date": "Date",
  "actual_delivery_date": "Date",
  "delivery_status": "String",
  "delivery_address": {
    "line1": "String",
    "line2": "String",
    "city": "String",
    "state": "String",
    "pincode": "String",
    "country": "String"
  },
  "assigned_agent": "String",
  "last_updated": "Date"
}
```

## Feedback

```json
{
  "_id": "ObjectId",
  "user_id": "String",
  "order_id": "String",
  "product_id": "String",
  "agent_id": "String",
  "rating": "Number",
  "review_text": "String",
  "feedback_type": "String",
  "submitted_at": "Date",
  "sentiment_analysis": {
    "score": "Number",
    "label": "String"
  }
}
```