# Agent Logic (rough)

## Recommendation
- reads: users, products
- writes: none
- input:
```json
{
  "user_id": "USER123",
  "constraints": {
    "category": "WOMEN",
    "subcategory": "TOPS",
    "colors": ["BLUE", "BLACK"],
    "price_range": [1000, 2000],
    "tags": ["ETHNIC", "CASUAL"]
  },
  "exclude_product_ids": ["SKU111", "SKU222"],
  "top_k": 5
}
```
- output: if recommendation found
```json
{
  "success": true,
  "recommendations": [
    {
      "product_id": "SKU123",
      "name": "Cotton Kurti",
      "category": "WOMEN",
      "subcategory": "TOPS",
      "price": 1499,
      "rating": 4.3,
      "image": "url1",
      "score": 7.15,
      "signals": ["POPULAR", "CATEGORY_MATCH"],
      "reason": "Matches your selected category and budget"
    }
  ],
  "applied_filters": {
    "category": "WOMEN",
    "subcategory": "TOPS",
    "price_range": [1000, 2000]
  }
}
```
- output if recommendation not found:
```json
{
  "success": false,
  "reason": "NO_MATCHING_PRODUCTS",
  "recommendations": []
}
```

## Inventory
- reads: inventory, products
- writes: none
- input:
```json
{
  "sku": "SKU123",
  "userLocation": "DELHI_STORE"
}
```


## Loyalty & Offers
- reads: users, offers
- writes: users, orders (DRAFT)

## Payment
- reads: orders
- writes: orders, payments

## Fulfillment
- reads: orders, inventory
- writes: orders, inventory, shipments

## Post Purchase
- reads: orders, shipments, payments
- writes: invoices, notifications
