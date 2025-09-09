from fastapi import FastAPI, APIRouter, HTTPException, File, UploadFile, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum
import csv
import io
import base64
import jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt


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

# Security setup
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


# Define Enums
class CarStatus(str, Enum):
    present = "present"
    absent = "absent"


class UserRole(str, Enum):
    admin = "admin"
    user = "user"


# Authentication Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    password_hash: str
    role: UserRole = UserRole.user
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None  # ID of admin who created this user


class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.user


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict


class UserResponse(BaseModel):
    id: str
    username: str
    role: UserRole
    created_at: datetime
    created_by: Optional[str]


# Password utilities
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = {"username": username}
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"username": token_data["username"]})
    if user is None:
        raise credentials_exception
    return User(**user)


async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


# Define Models
class Car(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    make: str
    model: str
    number: str  # Internal vehicle number instead of year
    purchase_date: Optional[str] = None  # Purchase date instead of price
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
    number: str
    purchase_date: Optional[str] = None
    image_url: Optional[str] = None
    vin: Optional[str] = None


class CarUpdate(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None
    number: Optional[str] = None
    purchase_date: Optional[str] = None
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


# Authentication routes
@api_router.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Login with username and password"""
    user = await db.users.find_one({"username": user_credentials.username})
    if not user or not verify_password(user_credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"]
        }
    }


@api_router.post("/auth/create-user", response_model=UserResponse)
async def create_user(user_data: UserCreate, current_admin: User = Depends(get_current_admin_user)):
    """Create a new user (admin only)"""
    # Check if username already exists
    existing_user = await db.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        password_hash=hashed_password,
        role=user_data.role,
        created_by=current_admin.id
    )
    
    user_mongo = prepare_for_mongo(new_user.dict())
    await db.users.insert_one(user_mongo)
    
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        role=new_user.role,
        created_at=new_user.created_at,
        created_by=new_user.created_by
    )


@api_router.get("/auth/users", response_model=List[UserResponse])
async def get_users(current_admin: User = Depends(get_current_admin_user)):
    """Get all users (admin only)"""
    users = await db.users.find().to_list(1000)
    return [UserResponse(**parse_from_mongo(user)) for user in users]


@api_router.delete("/auth/users/{user_id}")
async def delete_user(user_id: str, current_admin: User = Depends(get_current_admin_user)):
    """Delete a user (admin only)"""
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}


@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        created_at=current_user.created_at,
        created_by=current_user.created_by
    )


# Initialize default admin user
async def create_default_admin():
    """Create default admin user if no users exist"""
    user_count = await db.users.count_documents({})
    if user_count == 0:
        default_admin = User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            role=UserRole.admin
        )
        user_mongo = prepare_for_mongo(default_admin.dict())
        await db.users.insert_one(user_mongo)
        print("✅ Default admin user created: username='admin', password='admin123'")
        print("⚠️  Please change the default password after first login!")


# API Routes
@api_router.get("/")
async def root():
    return {"message": "Car Dealership Inventory API with Authentication"}


@api_router.post("/init-admin")
async def init_admin():
    """Initialize default admin user (for setup purposes)"""
    await create_default_admin()
    return {"message": "Admin initialization attempted"}


@api_router.post("/create-default-admin")
async def create_default_admin_force():
    """Force create default admin user"""
    default_admin = User(
        username="admin",
        password_hash=get_password_hash("admin123"),
        role=UserRole.admin
    )
    user_mongo = prepare_for_mongo(default_admin.dict())
    try:
        await db.users.insert_one(user_mongo)
        return {"message": "Default admin user created successfully"}
    except Exception as e:
        return {"message": f"Error creating admin: {str(e)}"}


@api_router.post("/cars", response_model=Car)
async def create_car(car_data: CarCreate, current_user: User = Depends(get_current_user)):
    """Create a new car in inventory"""
    car_dict = car_data.dict()
    car = Car(**car_dict)
    car_mongo = prepare_for_mongo(car.dict())
    
    await db.cars.insert_one(car_mongo)
    return car


@api_router.post("/cars/import-csv", response_model=CSVImportResult)
async def import_cars_from_csv(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
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
        expected_headers = {'make', 'model', 'number', 'purchase_date'}
        if not expected_headers.issubset(set(csv_reader.fieldnames or [])):
            missing_headers = expected_headers - set(csv_reader.fieldnames or [])
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required CSV columns: {', '.join(missing_headers)}. Required: make, model, number, purchase_date"
            )
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 for header row
            try:
                # Clean and validate required fields
                make = row.get('make', '').strip()
                model = row.get('model', '').strip()
                number_str = row.get('number', '').strip()
                purchase_date_str = row.get('purchase_date', '').strip()
                
                print(f"Processing row {row_num}: make={make}, model={model}, number={number_str}, purchase_date={purchase_date_str}")
                
                if not all([make, model, number_str]):
                    error_msg = f"Row {row_num}: Missing required fields (make={bool(make)}, model={bool(model)}, number={bool(number_str)})"
                    errors.append(error_msg)
                    print(f"Error: {error_msg}")
                    continue
                
                # Validate purchase_date format if provided (should be YYYY-MM-DD)
                if purchase_date_str:
                    try:
                        # Try to parse the date to validate format
                        from datetime import datetime
                        datetime.strptime(purchase_date_str, '%Y-%m-%d')
                    except ValueError:
                        try:
                            # Try alternative format DD.MM.YYYY or DD/MM/YYYY
                            if '.' in purchase_date_str:
                                date_parts = purchase_date_str.split('.')
                                if len(date_parts) == 3:
                                    purchase_date_str = f"{date_parts[2]}-{date_parts[1].zfill(2)}-{date_parts[0].zfill(2)}"
                            elif '/' in purchase_date_str:
                                date_parts = purchase_date_str.split('/')
                                if len(date_parts) == 3:
                                    purchase_date_str = f"{date_parts[2]}-{date_parts[1].zfill(2)}-{date_parts[0].zfill(2)}"
                            # Validate the converted date
                            datetime.strptime(purchase_date_str, '%Y-%m-%d')
                        except ValueError:
                            error_msg = f"Row {row_num}: Invalid purchase_date format. Use YYYY-MM-DD, DD.MM.YYYY, or DD/MM/YYYY"
                            errors.append(error_msg)
                            print(f"Error: {error_msg}")
                            continue
                
                # Create car object
                car_data = {
                    'make': make,
                    'model': model,
                    'number': number_str,
                    'purchase_date': purchase_date_str if purchase_date_str else None,
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
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user)
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
async def get_car(car_id: str, current_user: User = Depends(get_current_user)):
    """Get a specific car by ID"""
    car = await db.cars.find_one({"id": car_id})
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return Car(**parse_from_mongo(car))


@api_router.put("/cars/{car_id}", response_model=Car)
async def update_car(car_id: str, car_update: CarUpdate, current_user: User = Depends(get_current_user)):
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
async def update_car_status(car_id: str, status_update: StatusUpdate, current_user: User = Depends(get_current_user)):
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
async def delete_car(car_id: str, current_admin: User = Depends(get_current_admin_user)):
    """Delete a car from inventory (admin only)"""
    result = await db.cars.delete_one({"id": car_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Car not found")
    return {"message": "Car deleted successfully"}


@api_router.delete("/cars")
async def delete_all_cars(current_admin: User = Depends(get_current_admin_user)):
    """Delete all cars from inventory (admin only)"""
    result = await db.cars.delete_many({})
    return {
        "message": f"All cars deleted successfully",
        "deleted_count": result.deleted_count
    }


@api_router.get("/cars/stats/summary")
async def get_inventory_stats(current_user: User = Depends(get_current_user)):
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

@app.on_event("startup")
async def startup_event():
    await create_default_admin()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()