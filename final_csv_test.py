import requests
import json
import csv
import io
import uuid
from datetime import datetime

class FinalCSVImportTester:
    def __init__(self, base_url="https://dealership-tracker.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.auth_token = None
        self.created_car_ids = []

    def login(self):
        """Login as admin"""
        login_data = {"username": "admin", "password": "admin123"}
        response = requests.post(f"{self.base_url}/auth/login", json=login_data)
        if response.status_code == 200:
            self.auth_token = response.json()['access_token']
            return True
        return False

    def get_headers(self):
        """Get headers with auth token"""
        return {'Authorization': f'Bearer {self.auth_token}'}

    def create_csv_content(self, cars_data):
        """Create CSV content from car data"""
        output = io.StringIO()
        fieldnames = ['make', 'model', 'number', 'purchase_date', 'vin', 'image_url']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for car in cars_data:
            writer.writerow(car)
        return output.getvalue()

    def import_csv(self, csv_content):
        """Import CSV and return result"""
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        files = {'file': ('test.csv', csv_file, 'text/csv')}
        response = requests.post(f"{self.base_url}/cars/import-csv", files=files, headers=self.get_headers())
        return response.status_code == 200, response.json() if response.status_code == 200 else response.text

    def create_car(self, car_data):
        """Create a car via API"""
        response = requests.post(f"{self.base_url}/cars", json=car_data, headers=self.get_headers())
        if response.status_code == 200:
            car = response.json()
            self.created_car_ids.append(car['id'])
            return car
        return None

    def get_car_by_vin(self, vin):
        """Get car by VIN"""
        response = requests.get(f"{self.base_url}/cars", params={"search": vin}, headers=self.get_headers())
        if response.status_code == 200:
            cars = response.json()
            for car in cars:
                if car.get('vin') == vin:
                    return car
        return None

    def delete_car(self, car_id):
        """Delete a car"""
        response = requests.delete(f"{self.base_url}/cars/{car_id}", headers=self.get_headers())
        return response.status_code == 200

    def cleanup(self):
        """Clean up created cars"""
        for car_id in self.created_car_ids:
            self.delete_car(car_id)
        self.created_car_ids.clear()

def run_final_csv_import_test():
    """Run final comprehensive CSV import test"""
    print("🚗 Final CSV Import Duplicate VIN Enhancement Test")
    print("=" * 60)
    
    tester = FinalCSVImportTester()
    
    # Step 1: Login
    print("\n1. 🔐 Admin Login")
    if not tester.login():
        print("❌ Login failed")
        return False
    print("✅ Login successful")
    
    # Step 2: Create initial test cars with unique VINs
    print("\n2. 📝 Creating Initial Test Cars")
    unique_id = str(uuid.uuid4())[:8]
    
    initial_cars = [
        {
            "make": "BMW",
            "model": "X5",
            "number": f"BMW{unique_id}",
            "purchase_date": "2024-01-15",
            "vin": f"BMW{unique_id}VIN123456"
        },
        {
            "make": "Mercedes",
            "model": "C-Class",
            "number": f"MB{unique_id}",
            "purchase_date": "2024-02-20", 
            "vin": f"MB{unique_id}VIN789012"
        }
    ]
    
    created_cars = []
    for car_data in initial_cars:
        car = tester.create_car(car_data)
        if car:
            created_cars.append(car)
            print(f"✅ Created: {car['make']} {car['model']} (VIN: {car['vin']})")
    
    if len(created_cars) != 2:
        print("❌ Failed to create initial cars")
        return False
    
    # Step 3: Test CSV import with duplicate VINs (should update existing)
    print("\n3. 🔄 Testing CSV Import with Duplicate VINs")
    
    duplicate_vin_cars = [
        {
            "make": "BMW",
            "model": "X5 Updated",  # Changed
            "number": f"BMW{unique_id}-NEW",  # Changed
            "purchase_date": "2024-01-20",  # Changed
            "vin": f"BMW{unique_id}VIN123456",  # Same VIN
            "image_url": "https://example.com/bmw-updated.jpg"
        },
        {
            "make": "Mercedes-Benz",  # Changed
            "model": "C-Class AMG",  # Changed
            "number": f"MB{unique_id}-UPDATED",  # Changed
            "purchase_date": "2024-02-25",  # Changed
            "vin": f"MB{unique_id}VIN789012",  # Same VIN
            "image_url": "https://example.com/mercedes-updated.jpg"
        }
    ]
    
    csv_content = tester.create_csv_content(duplicate_vin_cars)
    print(f"📄 CSV Content:\n{csv_content}")
    
    success, result = tester.import_csv(csv_content)
    if not success:
        print(f"❌ CSV import failed: {result}")
        tester.cleanup()
        return False
    
    print(f"✅ CSV Import Result: {json.dumps(result, indent=2)}")
    
    # Verify result structure
    if (result.get('success') == True and 
        result.get('imported_count') == 0 and 
        result.get('updated_count') == 2 and
        'updated' in result.get('message', '').lower()):
        print("✅ Import result structure is correct")
    else:
        print("❌ Import result structure is incorrect")
        tester.cleanup()
        return False
    
    # Step 4: Verify data was actually updated
    print("\n4. 🔍 Verifying Data Updates")
    
    # Check BMW was updated
    bmw_car = tester.get_car_by_vin(f"BMW{unique_id}VIN123456")
    if bmw_car:
        if (bmw_car['model'] == 'X5 Updated' and 
            bmw_car['number'] == f"BMW{unique_id}-NEW" and
            bmw_car['purchase_date'] == '2024-01-20' and
            bmw_car['image_url'] == 'https://example.com/bmw-updated.jpg'):
            print("✅ BMW car was updated correctly")
        else:
            print(f"❌ BMW car update failed. Current data: {json.dumps(bmw_car, indent=2)}")
            tester.cleanup()
            return False
    else:
        print("❌ BMW car not found after update")
        tester.cleanup()
        return False
    
    # Check Mercedes was updated
    mercedes_car = tester.get_car_by_vin(f"MB{unique_id}VIN789012")
    if mercedes_car:
        if (mercedes_car['make'] == 'Mercedes-Benz' and
            mercedes_car['model'] == 'C-Class AMG' and 
            mercedes_car['number'] == f"MB{unique_id}-UPDATED" and
            mercedes_car['purchase_date'] == '2024-02-25' and
            mercedes_car['image_url'] == 'https://example.com/mercedes-updated.jpg'):
            print("✅ Mercedes car was updated correctly")
        else:
            print(f"❌ Mercedes car update failed. Current data: {json.dumps(mercedes_car, indent=2)}")
            tester.cleanup()
            return False
    else:
        print("❌ Mercedes car not found after update")
        tester.cleanup()
        return False
    
    # Step 5: Test mixed import (new + existing VINs)
    print("\n5. 🔀 Testing Mixed CSV Import (New + Existing VINs)")
    
    mixed_cars = [
        {
            "make": "Toyota",
            "model": "Camry",
            "number": f"TOY{unique_id}",
            "purchase_date": "2024-04-15",
            "vin": f"TOY{unique_id}VIN111111",  # New VIN
            "image_url": "https://example.com/toyota.jpg"
        },
        {
            "make": "Honda", 
            "model": "Civic",
            "number": f"HON{unique_id}",
            "purchase_date": "2024-05-20",
            "vin": f"HON{unique_id}VIN222222",  # New VIN
            "image_url": "https://example.com/honda.jpg"
        },
        {
            "make": "BMW",
            "model": "X5 Final Update",  # Update existing BMW again
            "number": f"BMW{unique_id}-FINAL",
            "purchase_date": "2024-01-25",
            "vin": f"BMW{unique_id}VIN123456",  # Existing VIN
            "image_url": "https://example.com/bmw-final.jpg"
        }
    ]
    
    mixed_csv_content = tester.create_csv_content(mixed_cars)
    print(f"📄 Mixed CSV Content:\n{mixed_csv_content}")
    
    success, mixed_result = tester.import_csv(mixed_csv_content)
    if not success:
        print(f"❌ Mixed CSV import failed: {mixed_result}")
        tester.cleanup()
        return False
    
    print(f"✅ Mixed CSV Import Result: {json.dumps(mixed_result, indent=2)}")
    
    # Verify mixed result
    if (mixed_result.get('success') == True and 
        mixed_result.get('imported_count') == 2 and 
        mixed_result.get('updated_count') == 1):
        print("✅ Mixed import result is correct (2 new, 1 updated)")
    else:
        print("❌ Mixed import result is incorrect")
        tester.cleanup()
        return False
    
    # Step 6: Verify final state
    print("\n6. 🎯 Verifying Final State")
    
    # Check new Toyota car
    toyota_car = tester.get_car_by_vin(f"TOY{unique_id}VIN111111")
    if toyota_car and toyota_car['make'] == 'Toyota':
        print("✅ New Toyota car created successfully")
    else:
        print("❌ New Toyota car not found")
        tester.cleanup()
        return False
    
    # Check new Honda car
    honda_car = tester.get_car_by_vin(f"HON{unique_id}VIN222222")
    if honda_car and honda_car['make'] == 'Honda':
        print("✅ New Honda car created successfully")
    else:
        print("❌ New Honda car not found")
        tester.cleanup()
        return False
    
    # Check BMW was updated again
    bmw_final = tester.get_car_by_vin(f"BMW{unique_id}VIN123456")
    if bmw_final and bmw_final['model'] == 'X5 Final Update':
        print("✅ BMW car was updated again successfully")
    else:
        print("❌ BMW car final update failed")
        tester.cleanup()
        return False
    
    # Step 7: Test error handling
    print("\n7. ⚠️ Testing Error Handling")
    
    invalid_csv = "make,model\nToyota,Prius\nHonda,Accord"
    success, error_result = tester.import_csv(invalid_csv)
    
    if not success and 'Missing required CSV columns' in str(error_result):
        print("✅ Invalid CSV properly rejected")
    else:
        print("❌ Invalid CSV was not properly rejected")
        tester.cleanup()
        return False
    
    # Cleanup
    print("\n8. 🧹 Cleaning Up")
    tester.cleanup()
    print("✅ Cleanup completed")
    
    return True

def main():
    """Main test function"""
    success = run_final_csv_import_test()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL CSV IMPORT TESTS PASSED!")
        print("✅ Duplicate VIN handling works correctly")
        print("✅ Existing cars are updated instead of causing errors")
        print("✅ Mixed imports (new + existing) work properly")
        print("✅ Import response includes both imported_count and updated_count")
        print("✅ Data integrity is maintained throughout the process")
        print("✅ Error handling works for invalid CSV files")
        print("\n🎯 CONCLUSION: The CSV import enhancement successfully resolves the duplicate VIN issue!")
        return 0
    else:
        print("❌ CSV IMPORT TESTS FAILED")
        print("❌ Issues remain with the duplicate VIN handling")
        return 1

if __name__ == "__main__":
    exit(main())