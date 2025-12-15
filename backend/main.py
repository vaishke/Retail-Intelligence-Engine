from fastapi import FastAPI
from routes.inventory_routes import router as inventory_router

app = FastAPI(
    title="Retail Agentic AI Backend",
    description="Agent-based backend for inventory, sales, and order intelligence",
    version="1.0.0"
)

# Register routers
app.include_router(inventory_router)
