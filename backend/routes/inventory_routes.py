from services.inventory_service import InventoryService
from fastapi import APIRouter, Body

router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"]
)

@router.post("/check_stock")
def check_stock(data: dict = Body(...)):
    product_id = data.get("product_id") or data.get("sku")
    store_id = data.get("store_id")

    return InventoryService.check_stock_service(product_id, store_id)


@router.post("/alternatives")
def check_alternatives(data: dict = Body(...)):
    category = data.get("category")
    budget = data.get("budget")

    return InventoryService.suggest_alternatives_service(category, budget)


@router.post("/store_stock")
def get_store_stock(data: dict = Body(...)):
    product_id = data.get("product_id") or data.get("sku")

    return InventoryService.get_store_stock_service(product_id)
