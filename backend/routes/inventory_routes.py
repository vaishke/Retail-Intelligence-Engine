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

    return InventoryService.check_stock_service(sku, userLocation)


@router.post("/alternatives")
def check_alternatives(data: dict = Body(...)):
    category = data.get("category")
    budget = data.get("budget")

    return InventoryService.suggest_alternatives_service(category, budget)


@router.post("/store_stock")
def get_store_stock(data: dict = Body(...)):
    sku = data.get("sku")

    return InventoryService.get_store_stock_service(sku)