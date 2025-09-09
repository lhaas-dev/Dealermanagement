from fastapi import FastAPI, APIRouter, HTTPException, File, UploadFile
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
import csv
import io
import base64


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
    status: CarStatus = CarStatus.absent  # Default to absent
    vin: Optional[str] = None
    car_photo: Optional[str] = None  # Base64 encoded photo of the car
    vin_photo: Optional[str] = None  # Base64 encoded photo of the VIN
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
    car_photo: Optional[str] = None  # Required when marking as present
    vin_photo: Optional[str] = None  # Required when marking as present


class CSVImportResult(BaseModel):
    success: bool
    imported_count: int
    errors: List[str] = []
    message: str


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


@api_router.post("/cars/import-csv", response_model=CSVImportResult)
async def import_cars_from_csv(file: UploadFile = File(...)):
    """Import cars from CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        content = await file.read()
        
        # Handle different encodings and BOM
        try:
            # Try UTF-8 with BOM first
            if content.startswith(b'\xef\xbb\xbf'):
                csv_data = content[3:].decode('utf-8')
            else:
                csv_data = content.decode('utf-8')
        except UnicodeDecodeError:
            # Fallback to other encodings
            try:
                csv_data = content.decode('utf-8-sig')  # This automatically handles BOM
            except UnicodeDecodeError:
                csv_data = content.decode('latin-1')
        
        # Remove any remaining BOM characters
        csv_data = csv_data.replace('\ufeff', '')
        
        # Debug logging
        print(f"CSV file received: {file.filename}, size: {len(content)} bytes")
        print(f"CSV content preview: {repr(csv_data[:100])}...")
        
        csv_reader = csv.DictReader(io.StringIO(csv_data))
        
        # Clean field names to remove any invisible characters and whitespace
        if csv_reader.fieldnames:
            cleaned_fieldnames = []
            for field in csv_reader.fieldnames:
                # Remove BOM, whitespace, and other invisible characters
                cleaned_field = field.strip().replace('\ufeff', '').replace('\x00', '')
                # Remove any non-printable ASCII characters except common ones
                cleaned_field = ''.join(char for char in cleaned_field if char.isprintable() or char in '\t\n\r')
                cleaned_fieldnames.append(cleaned_field)
            
            csv_reader.fieldnames = cleaned_fieldnames
            print(f"CSV fieldnames after cleaning: {csv_reader.fieldnames}")
        
        imported_count = 0
        errors = []
        
        # Check if CSV has required headers
        expected_headers = {'make', 'model', 'year', 'price'}
        if not expected_headers.issubset(set(csv_reader.fieldnames or [])):
            missing_headers = expected_headers - set(csv_reader.fieldnames or [])
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required CSV columns: {', '.join(missing_headers)}. Required: make, model, year, price"
            )
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 for header row
            try:
                # Clean and validate required fields
                make = row.get('make', '').strip()
                model = row.get('model', '').strip()
                year_str = row.get('year', '').strip()
                price_str = row.get('price', '').strip()
                
                print(f"Processing row {row_num}: make={make}, model={model}, year={year_str}, price={price_str}")
                
                if not all([make, model, year_str, price_str]):
                    error_msg = f"Row {row_num}: Missing required fields (make={bool(make)}, model={bool(model)}, year={bool(year_str)}, price={bool(price_str)})"
                    errors.append(error_msg)
                    print(f"Error: {error_msg}")
                    continue
                
                # Convert and validate data types
                try:
                    year = int(year_str)
                    if year < 1900 or year > 2030:
                        errors.append(f"Row {row_num}: Year {year} is not realistic (must be between 1900-2030)")
                        continue
                        
                    price = float(price_str.replace('$', '').replace(',', ''))
                    if price <= 0:
                        errors.append(f"Row {row_num}: Price must be greater than 0")
                        continue
                        
                except ValueError as ve:
                    error_msg = f"Row {row_num}: Invalid year or price format - {str(ve)}"
                    errors.append(error_msg)
                    print(f"Error: {error_msg}")
                    continue
                
                # Create car object
                car_data = {
                    'make': make,
                    'model': model,
                    'year': year,
                    'price': price,
                    'vin': row.get('vin', '').strip() or None,
                    'image_url': row.get('image_url', '').strip() or None,
                    'status': CarStatus.absent  # All imported cars start as absent
                }
                
                print(f"Creating car with data: {car_data}")
                
                # Check for duplicate VIN if VIN is provided
                if car_data['vin']:
                    existing_car = await db.cars.find_one({"vin": car_data['vin']})
                    if existing_car:
                        error_msg = f"Row {row_num}: Car with VIN '{car_data['vin']}' already exists"
                        errors.append(error_msg)
                        print(f"Error: {error_msg}")
                        continue
                
                car = Car(**car_data)
                car_mongo = prepare_for_mongo(car.dict())
                await db.cars.insert_one(car_mongo)
                imported_count += 1
                
                print(f"Successfully imported car: {make} {model}")
                
            except Exception as e:
                error_msg = f"Row {row_num}: {str(e)}"
                errors.append(error_msg)
                print(f"Exception: {error_msg}")
        
        result = CSVImportResult(
            success=True,
            imported_count=imported_count,
            errors=errors[:10],  # Limit errors to first 10
            message=f"Successfully imported {imported_count} cars"
        )
        
        print(f"Import complete: {imported_count} cars imported, {len(errors)} errors")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error processing CSV: {str(e)}"
        print(f"Fatal error: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


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
    """Update a car's presence status with photo verification"""
    car = await db.cars.find_one({"id": car_id})
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    
    # If marking as present, require both photos
    if status_update.status == CarStatus.present:
        if not status_update.car_photo or not status_update.vin_photo:
            raise HTTPException(
                status_code=400, 
                detail="Both car photo and VIN photo are required to mark car as present"
            )
    
    update_data = {
        "status": status_update.status,
        "updated_at": datetime.now(timezone.utc)
    }
    
    # Add photos if provided
    if status_update.car_photo:
        update_data["car_photo"] = status_update.car_photo
    if status_update.vin_photo:
        update_data["vin_photo"] = status_update.vin_photo
    
    # If marking as absent, clear photos
    if status_update.status == CarStatus.absent:
        update_data["car_photo"] = None
        update_data["vin_photo"] = None
    
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