import requests
import sys
import json
import base64
import os
from datetime import datetime

class CarDealershipAPITester:
    def __init__(self, base_url="https://dealership-tracker.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.created_car_ids = []

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}" if endpoint else self.base_url
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root Endpoint", "GET", "", 200)

    def test_create_car(self, car_data):
        """Test creating a new car"""
        success, response = self.run_test(
            "Create Car",
            "POST",
            "cars",
            200,
            data=car_data
        )
        if success and 'id' in response:
            self.created_car_ids.append(response['id'])
            return response['id']
        return None

    def test_get_all_cars(self):
        """Test getting all cars"""
        return self.run_test("Get All Cars", "GET", "cars", 200)

    def test_get_car_by_id(self, car_id):
        """Test getting a specific car by ID"""
        return self.run_test(
            f"Get Car by ID ({car_id[:8]}...)",
            "GET",
            f"cars/{car_id}",
            200
        )

    def test_update_car(self, car_id, update_data):
        """Test updating a car"""
        return self.run_test(
            f"Update Car ({car_id[:8]}...)",
            "PUT",
            f"cars/{car_id}",
            200,
            data=update_data
        )

    def test_update_car_status(self, car_id, status, car_photo=None, vin_photo=None):
        """Test updating car status with optional photo verification"""
        data = {"status": status}
        if car_photo:
            data["car_photo"] = car_photo
        if vin_photo:
            data["vin_photo"] = vin_photo
            
        return self.run_test(
            f"Update Car Status to {status} ({car_id[:8]}...)",
            "PATCH",
            f"cars/{car_id}/status",
            200 if (status == "absent" or (car_photo and vin_photo)) else 400,
            data=data
        )

    def test_search_cars(self, search_term):
        """Test searching cars"""
        return self.run_test(
            f"Search Cars ('{search_term}')",
            "GET",
            "cars",
            200,
            params={"search": search_term}
        )

    def test_filter_cars_by_status(self, status):
        """Test filtering cars by status"""
        return self.run_test(
            f"Filter Cars by Status ({status})",
            "GET",
            "cars",
            200,
            params={"status": status}
        )

    def test_get_stats(self):
        """Test getting inventory statistics"""
        return self.run_test("Get Inventory Stats", "GET", "cars/stats/summary", 200)

    def test_delete_car(self, car_id):
        """Test deleting a car"""
        success, response = self.run_test(
            f"Delete Car ({car_id[:8]}...)",
            "DELETE",
            f"cars/{car_id}",
            200
        )
        if success and car_id in self.created_car_ids:
            self.created_car_ids.remove(car_id)
        return success, response

    def test_csv_import(self, csv_file_path):
        """Test CSV import functionality"""
        print(f"\n🔍 Testing CSV Import...")
        print(f"   File: {csv_file_path}")
        
        try:
            url = f"{self.base_url}/cars/import-csv"
            
            with open(csv_file_path, 'rb') as f:
                files = {'file': ('sample_inventory.csv', f, 'text/csv')}
                response = requests.post(url, files=files)
            
            self.tests_run += 1
            success = response.status_code == 200
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_photo_verification_required(self, car_id):
        """Test that photo verification is required for marking as present"""
        # Test without photos (should fail)
        success1, _ = self.run_test(
            f"Mark Present Without Photos (should fail) ({car_id[:8]}...)",
            "PATCH",
            f"cars/{car_id}/status",
            400,
            data={"status": "present"}
        )
        
        # Test with only car photo (should fail)
        success2, _ = self.run_test(
            f"Mark Present With Only Car Photo (should fail) ({car_id[:8]}...)",
            "PATCH",
            f"cars/{car_id}/status",
            400,
            data={"status": "present", "car_photo": "fake_base64_data"}
        )
        
        # Test with only VIN photo (should fail)
        success3, _ = self.run_test(
            f"Mark Present With Only VIN Photo (should fail) ({car_id[:8]}...)",
            "PATCH",
            f"cars/{car_id}/status",
            400,
            data={"status": "present", "vin_photo": "fake_base64_data"}
        )
        
        return success1 and success2 and success3

    def test_photo_verification_success(self, car_id):
        """Test successful photo verification"""
        # Create fake base64 image data
        fake_image_data = base64.b64encode(b"fake_image_data").decode('utf-8')
        
        return self.run_test(
            f"Mark Present With Both Photos ({car_id[:8]}...)",
            "PATCH",
            f"cars/{car_id}/status",
            200,
            data={
                "status": "present",
                "car_photo": fake_image_data,
                "vin_photo": fake_image_data
            }
        )

    def test_default_status_absent(self):
        """Test that new cars default to absent status"""
        car_data = {
            "make": "Test",
            "model": "DefaultStatus",
            "year": 2023,
            "price": 25000.00,
            "vin": "TEST123456789"
        }
        
        success, response = self.run_test(
            "Create Car (should default to absent)",
            "POST",
            "cars",
            200,
            data=car_data
        )
        
        if success and response.get('status') == 'absent':
            print("✅ Car correctly defaults to 'absent' status")
            if 'id' in response:
                self.created_car_ids.append(response['id'])
            return True, response
        elif success:
            print(f"❌ Car status is '{response.get('status')}', expected 'absent'")
            return False, response
        else:
            return False, {}

    def test_mark_absent_clears_photos(self, car_id):
        """Test that marking as absent clears stored photos"""
        return self.run_test(
            f"Mark Absent (should clear photos) ({car_id[:8]}...)",
            "PATCH",
            f"cars/{car_id}/status",
            200,
            data={"status": "absent"}
        )

    def test_nonexistent_car(self):
        """Test getting a non-existent car"""
        fake_id = "nonexistent-car-id"
        return self.run_test(
            "Get Non-existent Car (should fail)",
            "GET",
            f"cars/{fake_id}",
            404
        )

    def cleanup(self):
        """Clean up created test data"""
        print(f"\n🧹 Cleaning up {len(self.created_car_ids)} test cars...")
        for car_id in self.created_car_ids.copy():
            self.test_delete_car(car_id)

def main():
    print("🚗 Starting Enhanced Car Dealership API Tests")
    print("=" * 60)
    
    tester = CarDealershipAPITester()
    
    # Test 1: Root endpoint
    tester.test_root_endpoint()
    
    # Test 2: CSV Import functionality
    csv_file_path = "/app/sample_inventory.csv"
    if os.path.exists(csv_file_path):
        print(f"\n📁 Testing CSV Import with {csv_file_path}")
        success, import_result = tester.test_csv_import(csv_file_path)
        if success:
            print(f"✅ CSV Import successful: {import_result.get('imported_count', 0)} cars imported")
        else:
            print("❌ CSV Import failed")
    else:
        print(f"⚠️  CSV file not found at {csv_file_path}")
    
    # Test 3: Verify default status is absent for new cars
    print(f"\n🔍 Testing Default Status Behavior")
    tester.test_default_status_absent()
    
    # Test 4: Create additional test cars
    test_cars = [
        {
            "make": "Toyota",
            "model": "Camry",
            "year": 2023,
            "price": 28500.00,
            "image_url": "https://example.com/camry.jpg",
            "vin": "1HGBH41JXMN109186"
        },
        {
            "make": "Honda",
            "model": "Civic",
            "year": 2022,
            "price": 24000.00,
            "vin": "2HGFC2F59NH123456"
        }
    ]
    
    created_car_ids = []
    for i, car_data in enumerate(test_cars):
        car_id = tester.test_create_car(car_data)
        if car_id:
            created_car_ids.append(car_id)
    
    # Test 5: Get all cars
    tester.test_get_all_cars()
    
    # Test 6: Get individual cars
    for car_id in created_car_ids:
        tester.test_get_car_by_id(car_id)
    
    # Test 7: Update car
    if created_car_ids:
        update_data = {
            "make": "Toyota",
            "model": "Camry Hybrid",
            "year": 2023,
            "price": 32000.00
        }
        tester.test_update_car(created_car_ids[0], update_data)
    
    # Test 8: Photo Verification Tests
    if created_car_ids:
        print(f"\n📸 Testing Photo Verification Requirements")
        
        # Test that photos are required for marking as present
        tester.test_photo_verification_required(created_car_ids[0])
        
        # Test successful photo verification
        tester.test_photo_verification_success(created_car_ids[0])
        
        # Test marking as absent (should clear photos)
        tester.test_mark_absent_clears_photos(created_car_ids[0])
    
    # Test 9: Search functionality
    tester.test_search_cars("Toyota")
    tester.test_search_cars("Civic")
    tester.test_search_cars("1HGBH41JXMN109186")  # Search by VIN
    
    # Test 10: Filter by status
    tester.test_filter_cars_by_status("present")
    tester.test_filter_cars_by_status("absent")
    
    # Test 11: Get statistics
    tester.test_get_stats()
    
    # Test 12: Error handling - non-existent car
    tester.test_nonexistent_car()
    
    # Test 13: Delete functionality (enhanced test)
    print(f"\n🗑️  Testing Delete Functionality")
    for car_id in created_car_ids:
        tester.test_delete_car(car_id)
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"❌ {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())