from services.inventory_service import InventoryService
from fastapi import APIRouter, Body

router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"]
)

@router.post("/check_stock")
def check_stock(data: dict = Body(...)):
    sku = data.get("sku")
    userLocation = data.get("userLocation")

    if not sku or not userLocation:
        return {
            "status": "error",
            "message": "sku and userLocation are required"
        }
    return InventoryService.check_stock_service(sku, userLocation)

@router.post("/alternatives")
def check_alternatives(data: dict = Body(...)):
    category = data.get("category")
    budget = data.get("budget")

    if not category or budget is None:
        return {
            "status": "error",
            "message": "category and budget are required"
        }
    return InventoryService.suggest_alternatives_service(category, budget)

@router.post("/store-stock")
def get_store_stock(data: dict = Body(...)):
    sku = data.get("sku")
    if not sku:
        return {
            "status": "error",
            "message": "sku are required"
        }
    return InventoryService.get_store_stock_service(sku)
