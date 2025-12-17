from sales_graph.graph import build_sales_graph

app = build_sales_graph()

initial_state = {
    "user_id": "USER123",
    "constraints": {
        "category": "WOMEN",
        "subcategory": "TOPS",
        "price_range": [1000, 2000]
    }
}

result = app.invoke(initial_state)
print(result)
