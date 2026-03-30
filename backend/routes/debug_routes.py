from fastapi import APIRouter
from db.database import db
from bson import ObjectId

router = APIRouter(prefix="/debug", tags=["Debug"])

# ✅ ADD THIS FUNCTION HERE
def serialize(data):
    if isinstance(data, list):
        return [serialize(item) for item in data]
    
    if isinstance(data, dict):
        return {key: serialize(value) for key, value in data.items()}
    
    if isinstance(data, ObjectId):
        return str(data)
    
    return data

# ✅ YOUR API
@router.get("/db")
def print_database():
    result = {}

    for collection_name in db.list_collection_names():
        collection = db[collection_name]
        data = [serialize(doc) for doc in collection.find()]
        result[collection_name] = data

    return result