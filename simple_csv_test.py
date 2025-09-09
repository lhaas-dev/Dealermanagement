import requests
import json
import csv
import io
from datetime import datetime

# Test the CSV import functionality with a simple test
base_url = "https://dealership-tracker.preview.emergentagent.com/api"

# Login first
login_data = {"username": "admin", "password": "admin123"}
response = requests.post(f"{base_url}/auth/login", json=login_data)
token = response.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

print("🔍 Testing CSV Import Update Functionality")
print("=" * 50)

# Step 1: Create a test car
print("\n1. Creating initial test car...")
car_data = {
    "make": "TestMake",
    "model": "TestModel", 
    "number": "TEST001",
    "purchase_date": "2024-01-01",
    "vin": "TEST123456789"
}

response = requests.post(f"{base_url}/cars", json=car_data, headers=headers)
if response.status_code == 200:
    initial_car = response.json()
    print(f"✅ Created car: {initial_car['make']} {initial_car['model']}")
    print(f"   Initial updated_at: {initial_car['updated_at']}")
    car_id = initial_car['id']
else:
    print(f"❌ Failed to create car: {response.text}")
    exit(1)

# Step 2: Import CSV with same VIN but different data
print("\n2. Importing CSV with same VIN but updated data...")
csv_data = [
    {
        "make": "UpdatedMake",
        "model": "UpdatedModel",
        "number": "TEST001-UPDATED", 
        "purchase_date": "2024-01-15",
        "vin": "TEST123456789",
        "image_url": "https://example.com/updated.jpg"
    }
]

# Create CSV content
output = io.StringIO()
fieldnames = ['make', 'model', 'number', 'purchase_date', 'vin', 'image_url']
writer = csv.DictWriter(output, fieldnames=fieldnames)
writer.writeheader()
for car in csv_data:
    writer.writerow(car)

csv_content = output.getvalue()
print(f"CSV Content:\n{csv_content}")

# Upload CSV
csv_file = io.BytesIO(csv_content.encode('utf-8'))
files = {'file': ('test.csv', csv_file, 'text/csv')}

response = requests.post(f"{base_url}/cars/import-csv", files=files, headers=headers)
if response.status_code == 200:
    import_result = response.json()
    print(f"✅ CSV Import Result: {json.dumps(import_result, indent=2)}")
else:
    print(f"❌ CSV Import failed: {response.text}")
    exit(1)

# Step 3: Verify the car was updated
print("\n3. Verifying car was updated...")
response = requests.get(f"{base_url}/cars/{car_id}", headers=headers)
if response.status_code == 200:
    updated_car = response.json()
    print(f"Updated car data: {json.dumps(updated_car, indent=2)}")
    
    # Check if data was actually updated
    if updated_car['make'] == 'UpdatedMake':
        print("✅ Make was updated correctly")
    else:
        print(f"❌ Make not updated: expected 'UpdatedMake', got '{updated_car['make']}'")
    
    if updated_car['model'] == 'UpdatedModel':
        print("✅ Model was updated correctly")
    else:
        print(f"❌ Model not updated: expected 'UpdatedModel', got '{updated_car['model']}'")
        
    if updated_car['number'] == 'TEST001-UPDATED':
        print("✅ Number was updated correctly")
    else:
        print(f"❌ Number not updated: expected 'TEST001-UPDATED', got '{updated_car['number']}'")
        
    if updated_car['image_url'] == 'https://example.com/updated.jpg':
        print("✅ Image URL was updated correctly")
    else:
        print(f"❌ Image URL not updated: expected 'https://example.com/updated.jpg', got '{updated_car['image_url']}'")
        
    # Check updated_at timestamp
    initial_time = datetime.fromisoformat(initial_car['updated_at'].replace('Z', '+00:00'))
    updated_time = datetime.fromisoformat(updated_car['updated_at'].replace('Z', '+00:00'))
    
    if updated_time > initial_time:
        print(f"✅ Updated timestamp is newer: {updated_car['updated_at']}")
    else:
        print(f"❌ Updated timestamp not changed: {updated_car['updated_at']}")
        
else:
    print(f"❌ Failed to get updated car: {response.text}")

# Step 4: Clean up
print("\n4. Cleaning up...")
response = requests.delete(f"{base_url}/cars/{car_id}", headers=headers)
if response.status_code == 200:
    print("✅ Test car deleted")
else:
    print(f"❌ Failed to delete test car: {response.text}")

print("\n" + "=" * 50)
print("Test completed!")