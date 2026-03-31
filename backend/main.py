# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId

# ✅ Import MongoDB collections
from db.database import products_collection

# ✅ Import routers
from routes.sales_agent_routes import router as sales_router
from routes.inventory_routes import router as inventory_router
from routes.offer_loyalty_routes import router as offer_router
from routes.payment_route import router as payment_router
from routes.recommendation_routes import router as recommendation_router
from routes.post_purchase_route import router as post_purchase_router
from routes.fulfillment_routes import router as fulfillment_router
from routes.debug_routes import router as debug_router
from routes.user_auth_routes import router as auth_router

app = FastAPI(
    title="Retail Agentic AI Backend",
    description="Agent-based backend for inventory, sales, and order intelligence",
    version="1.0.0"
)

# ✅ Include debug router first (optional)
app.include_router(debug_router)

# ✅ CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Register all routers
app.include_router(sales_router)
app.include_router(inventory_router)
app.include_router(offer_router)
app.include_router(payment_router)
app.include_router(recommendation_router)
app.include_router(post_purchase_router)
app.include_router(fulfillment_router)
app.include_router(auth_router)

# ✅ Root endpoint
@app.get("/", tags=["Health"])
def root():
    return {
        "status": "ok",
        "chat_endpoint": "POST /sales/chat",
        "docs": "GET /docs"
    }

# ✅ Health check
@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}


# -------------------------------
# Products endpoint
# -------------------------------
def serialize_product(product):
    """Convert MongoDB document to JSON-serializable dict."""
    product["_id"] = str(product["_id"])
    return product


@app.get("/products")
def get_products():
    try:
        products = list(products_collection.find())
        return [serialize_product(p) for p in products]
    except Exception as e:
        return {"error": str(e)}