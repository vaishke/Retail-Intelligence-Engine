from fastapi import FastAPI
from routes.inventory_routes import router as inventory_router
from routes.offer_loyalty_routes import router as offer_router
from routes.payment_route import router as payment_router
from routes.recommendation_routes import router as recommendation_router

app = FastAPI(
    title="Retail Agentic AI Backend",
    description="Agent-based backend for inventory, sales, and order intelligence",
    version="1.0.0"
)

# Register routers
app.include_router(inventory_router)
app.include_router(offer_router)
app.include_router(payment_router)
app.include_router(recommendation_router)
