# Retail_AI Database Schema

## users

```json
{
  "_id": "USER123",
  "name": "Ananya",
  "email": "ananya@example.com",
  "phone": "+91XXXXXXXXXX",
  "loyalty_tier": "SILVER | GOLD | PLATINUM",
  "created_at": "timestamp"
}
```

## sessions

```json
{
  "_id": "SESSION123",
  "user_id": "USER123",
  "active_channel": "WEB | MOBILE | KIOSK | WHATSAPP | VOICE",
  "context": {
    "intent": "BROWSE | PURCHASE | RETURN",
    "current_category": "WOMEN_TOPS",
    "selected_products": ["SKU123"],
    "cart_order_id": "ORD456",
    "last_agent": "RECOMMENDATION",
    "last_step": "STOCK_CONFIRMED"
  },
  "channel_history": [
    { "channel": "MOBILE", "at": "timestamp" },
    { "channel": "KIOSK", "at": "timestamp" }
  ],
  "updated_at": "timestamp"
}

```

## products

```json
{
  "_id": "SKU123",
  "name": "Cotton Kurti",
  "category": "WOMEN",
  "subcategory": "TOPS",
  "attributes": {
    "color": "BLUE",
    "size": ["S", "M", "L"]
  },
  "tags": ["ETHNIC", "CASUAL"],
  "price": 1499,
  "rating": 4.3,
  "images": ["url1"],
  "active": true
}
```

## inventory

```json
{
  "_id": "INV123",
  "product_id": "SKU123",
  "location": "WAREHOUSE | STORE_001",
  "available_qty": 12,
  "last_updated": "timestamp"
}
```

## orders

```json
{
  "_id": "ORD456",
  "user_id": "USER123",
  "items": [
    {
      "product_id": "SKU123",
      "qty": 1,
      "price": 1499
    }
  ],
  "subtotal": 1499,
  "discount": 200,
  "final_amount": 1299,
  "status": "CREATED | PAYMENT_PENDING | PAID | CONFIRMED | FULFILLED | CLOSED",
  "fulfillment_type": "SHIP_TO_HOME | CLICK_AND_COLLECT | TRY_IN_STORE",
  "created_at": "timestamp"
}
```

## payments

```json
{
  "_id": "PAY123",
  "order_id": "ORD456",
  "method": "UPI | CARD | GIFT_CARD | POS",
  "amount": 1299,
  "status": "SUCCESS | FAILED | PENDING",
  "transaction_ref": "TXN789",
  "timestamp": "timestamp"
}
```

## offers

```json
{
  "_id": "OFF123",
  "type": "PERCENTAGE | FLAT",
  "value": 10,
  "applicable_categories": ["WOMEN"],
  "valid_until": "timestamp"
}
```

## loyalty

```json
{
  "_id": "LOY123",
  "user_id": "USER123",
  "points": 320,
  "last_updated": "timestamp"
}
```

## shipments

```json
{
  "_id": "SHIP123",
  "order_id": "ORD456",
  "status": "PENDING | DISPATCHED | DELIVERED",
  "tracking_id": "TRACK123"
}
```

## invoices

```json
{
  "_id": "INV789",
  "order_id": "ORD456",
  "invoice_url": "pdf_link",
  "created_at": "timestamp"
}
```

## notifications

```json
{
  "_id": "NOTIF123",
  "user_id": "USER123",
  "type": "ORDER_CONFIRMATION | DELIVERY_UPDATE | FEEDBACK",
  "message": "Your order has been shipped",
  "sent_at": "timestamp"
}
```

