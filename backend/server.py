from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from enum import Enum


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Enums
class CarStatus(str, Enum):
    present = "present"
    absent = "absent"


# Define Models
class Car(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    make: str
    model: str
    year: int
    price: float
    image_url: Optional[str] = None
    status: CarStatus = CarStatus.present
    vin: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CarCreate(BaseModel):
    make: str
    model: str
    year: int
    price: float
    image_url: Optional[str] = None
    vin: Optional[str] = None


class CarUpdate(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    status: Optional[CarStatus] = None
    vin: Optional[str] = None


class StatusUpdate(BaseModel):
    status: CarStatus


# Helper functions
def prepare_for_mongo(data):
    """Convert datetime objects to ISO strings for MongoDB storage"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
    return data


def parse_from_mongo(item):
    """Parse datetime strings back from MongoDB"""
    if isinstance(item, dict):
        for key, value in item.items():
            if key in ['created_at', 'updated_at'] and isinstance(value, str):
                item[key] = datetime.fromisoformat(value)
    return item


# API Routes
@api_router.get("/")
async def root():
    return {"message": "Car Dealership Inventory API"}


@api_router.post("/cars", response_model=Car)
async def create_car(car_data: CarCreate):
    """Create a new car in inventory"""
    car_dict = car_data.dict()
    car = Car(**car_dict)
    car_mongo = prepare_for_mongo(car.dict())
    
    await db.cars.insert_one(car_mongo)
    return car


@api_router.get("/cars", response_model=List[Car])
async def get_cars(
    make: Optional[str] = None,
    model: Optional[str] = None,
    status: Optional[CarStatus] = None,
    search: Optional[str] = None
):
    """Get all cars with optional filtering"""
    query = {}
    
    # Add filters
    if make:
        query["make"] = {"$regex": make, "$options": "i"}
    if model:
        query["model"] = {"$regex": model, "$options": "i"}
    if status:
        query["status"] = status
    if search:
        query["$or"] = [
            {"make": {"$regex": search, "$options": "i"}},
            {"model": {"$regex": search, "$options": "i"}},
            {"vin": {"$regex": search, "$options": "i"}}
        ]
    
    cars = await db.cars.find(query).to_list(1000)
    return [Car(**parse_from_mongo(car)) for car in cars]


@api_router.get("/cars/{car_id}", response_model=Car)
async def get_car(car_id: str):
    """Get a specific car by ID"""
    car = await db.cars.find_one({"id": car_id})
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return Car(**parse_from_mongo(car))


@api_router.put("/cars/{car_id}", response_model=Car)
async def update_car(car_id: str, car_update: CarUpdate):
    """Update a car's information"""
    car = await db.cars.find_one({"id": car_id})
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    
    update_data = {k: v for k, v in car_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    update_mongo = prepare_for_mongo(update_data)
    await db.cars.update_one({"id": car_id}, {"$set": update_mongo})
    
    updated_car = await db.cars.find_one({"id": car_id})
    return Car(**parse_from_mongo(updated_car))


@api_router.patch("/cars/{car_id}/status", response_model=Car)
async def update_car_status(car_id: str, status_update: StatusUpdate):
    """Update a car's presence status"""
    car = await db.cars.find_one({"id": car_id})
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    
    update_data = {
        "status": status_update.status,
        "updated_at": datetime.now(timezone.utc)
    }
    
    update_mongo = prepare_for_mongo(update_data)
    await db.cars.update_one({"id": car_id}, {"$set": update_mongo})
    
    updated_car = await db.cars.find_one({"id": car_id})
    return Car(**parse_from_mongo(updated_car))


@api_router.delete("/cars/{car_id}")
async def delete_car(car_id: str):
    """Delete a car from inventory"""
    result = await db.cars.delete_one({"id": car_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Car not found")
    return {"message": "Car deleted successfully"}


@api_router.get("/cars/stats/summary")
async def get_inventory_stats():
    """Get inventory summary statistics"""
    total_cars = await db.cars.count_documents({})
    present_cars = await db.cars.count_documents({"status": "present"})
    absent_cars = await db.cars.count_documents({"status": "absent"})
    
    return {
        "total_cars": total_cars,
        "present_cars": present_cars,
        "absent_cars": absent_cars,
        "present_percentage": round((present_cars / total_cars * 100) if total_cars > 0 else 0, 1)
    }


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()