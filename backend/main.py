# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.database import products_collection

from routes.sales_agent_routes import router as sales_router
from routes.inventory_routes import router as inventory_router
from routes.offer_loyalty_routes import router as offer_router
from routes.payment_route import router as payment_router
from routes.recommendation_routes import router as recommendation_router
from routes.post_purchase_route import router as post_purchase_router
from routes.fulfillment_routes import router as fulfillment_router
from routes.debug_routes import router as debug_router
from routes.user_auth_routes import router as auth_router
from routes.cart_routes import router as cart_router
from routes.order_routes import router as order_router

from dotenv import load_dotenv
import os

app = FastAPI(
    title="Retail Agentic AI Backend",
    description="Agent-based backend for inventory, sales, and order intelligence",
    version="1.0.0"
)

load_dotenv()

print("os jwt: ", os.getenv("JWT_SECRET"))


def _get_allowed_origins() -> list[str]:
    configured = os.getenv("CORS_ALLOWED_ORIGINS", "")
    origins = [origin.strip() for origin in configured.split(",") if origin.strip()]
    if origins:
        return origins

    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

app.include_router(debug_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sales_router)
app.include_router(inventory_router)
app.include_router(offer_router)
app.include_router(payment_router)
app.include_router(recommendation_router)
app.include_router(post_purchase_router)
app.include_router(fulfillment_router)
app.include_router(auth_router)
app.include_router(cart_router)
app.include_router(order_router)

@app.get("/", tags=["Health"])
def root():
    return {
        "status": "ok",
        "chat_endpoint": "POST /sales/chat",
        "docs": "GET /docs"
    }

@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}


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
