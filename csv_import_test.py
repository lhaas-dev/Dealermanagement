import requests
import sys
import json
import csv
import io
import os
from datetime import datetime

class CSVImportTester:
    def __init__(self, base_url="https://dealership-tracker.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.created_car_ids = []
        self.auth_token = None
        self.auth_headers = {'Content-Type': 'application/json'}

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None, files=None, use_auth=True):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}" if endpoint else self.base_url
        headers = {}
        
        if use_auth and self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
        
        # Don't set Content-Type for file uploads
        if not files and use_auth:
            headers['Content-Type'] = 'application/json'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, headers=headers)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
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

    def test_admin_login(self, username="admin", password="admin123"):
        """Test admin login and store JWT token"""
        login_data = {
            "username": username,
            "password": password
        }
        
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data=login_data,
            use_auth=False
        )
        
        if success and 'access_token' in response:
            self.auth_token = response['access_token']
            print(f"✅ JWT Token obtained and stored")
            return True, response
        else:
            print(f"❌ Failed to obtain JWT token")
            return False, {}

    def create_csv_content(self, cars_data):
        """Create CSV content from car data"""
        output = io.StringIO()
        fieldnames = ['make', 'model', 'number', 'purchase_date', 'vin', 'image_url']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        
        writer.writeheader()
        for car in cars_data:
            writer.writerow(car)
        
        return output.getvalue()

    def test_csv_import(self, csv_content, test_name="CSV Import"):
        """Test CSV import functionality"""
        print(f"\n🔍 Testing {test_name}...")
        
        try:
            url = f"{self.base_url}/cars/import-csv"
            
            # Create a file-like object from CSV content
            csv_file = io.BytesIO(csv_content.encode('utf-8'))
            files = {'file': ('test_import.csv', csv_file, 'text/csv')}
            
            headers = {}
            if self.auth_token:
                headers['Authorization'] = f'Bearer {self.auth_token}'
            
            response = requests.post(url, files=files, headers=headers)
            
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

    def create_test_car(self, car_data):
        """Create a test car via API"""
        success, response = self.run_test(
            f"Create Test Car ({car_data.get('make', 'Unknown')} {car_data.get('model', 'Unknown')})",
            "POST",
            "cars",
            200,
            data=car_data
        )
        
        if success and 'id' in response:
            self.created_car_ids.append(response['id'])
            return response
        return None

    def get_car_by_vin(self, vin):
        """Get car by VIN using search"""
        success, response = self.run_test(
            f"Search Car by VIN ({vin})",
            "GET",
            "cars",
            200,
            params={"search": vin}
        )
        
        if success and isinstance(response, list) and len(response) > 0:
            # Find exact VIN match
            for car in response:
                if car.get('vin') == vin:
                    return car
        return None

    def verify_car_updated(self, vin, expected_data):
        """Verify that a car with given VIN has been updated with expected data"""
        car = self.get_car_by_vin(vin)
        if not car:
            print(f"❌ Car with VIN {vin} not found")
            return False
        
        print(f"🔍 Verifying car update for VIN {vin}...")
        
        # Check if updated_at timestamp exists and is valid
        if 'updated_at' in car:
            try:
                updated_time = datetime.fromisoformat(car['updated_at'].replace('Z', '+00:00'))
                print(f"✅ Updated timestamp is valid: {car['updated_at']}")
            except Exception as e:
                print(f"❌ Invalid updated_at format: {e}")
                return False
        
        # Verify expected data fields
        for field, expected_value in expected_data.items():
            if field in car:
                if car[field] == expected_value:
                    print(f"✅ Field '{field}' correctly updated to: {expected_value}")
                else:
                    print(f"❌ Field '{field}' mismatch - expected: {expected_value}, got: {car[field]}")
                    return False
            else:
                print(f"❌ Field '{field}' not found in car data")
                return False
        
        return True

    def cleanup(self):
        """Clean up created test data"""
        print(f"\n🧹 Cleaning up {len(self.created_car_ids)} test cars...")
        for car_id in self.created_car_ids.copy():
            success, _ = self.run_test(
                f"Delete Test Car ({car_id[:8]}...)",
                "DELETE",
                f"cars/{car_id}",
                200
            )
            if success:
                self.created_car_ids.remove(car_id)

def run_csv_import_duplicate_vin_tests():
    """Run comprehensive CSV import tests focusing on duplicate VIN handling"""
    print("📁 Starting CSV Import Duplicate VIN Tests")
    print("=" * 60)
    
    tester = CSVImportTester()
    
    # Test 1: Authentication Setup
    print(f"\n🔐 AUTHENTICATION SETUP")
    print("-" * 40)
    
    success, login_response = tester.test_admin_login("admin", "admin123")
    if not success:
        print("❌ CRITICAL: Admin login failed - cannot proceed with CSV import tests")
        return 1
    
    print("✅ Admin authentication successful")
    
    # Test 2: Create Initial Test Cars with Specific VINs
    print(f"\n📝 CREATING INITIAL TEST CARS")
    print("-" * 40)
    
    initial_cars = [
        {
            "make": "BMW",
            "model": "X5",
            "number": "BMW001",
            "purchase_date": "2024-01-15",
            "vin": "WBAFR7C50BC123456"
        },
        {
            "make": "Mercedes",
            "model": "C-Class", 
            "number": "MB002",
            "purchase_date": "2024-02-20",
            "vin": "WDDGF4HB1CA123789"
        },
        {
            "make": "Audi",
            "model": "A4",
            "number": "AUDI003",
            "purchase_date": "2024-03-10",
            "vin": "WAUZZZ8K1DA123456"
        }
    ]
    
    created_cars = []
    for car_data in initial_cars:
        car = tester.create_test_car(car_data)
        if car:
            created_cars.append(car)
            print(f"✅ Created initial car: {car['make']} {car['model']} (VIN: {car['vin']})")
    
    if len(created_cars) != len(initial_cars):
        print("❌ CRITICAL: Failed to create all initial test cars")
        tester.cleanup()
        return 1
    
    # Test 3: CSV Import with Duplicate VINs (Should Update Existing Cars)
    print(f"\n🔄 TESTING CSV IMPORT WITH DUPLICATE VINS")
    print("-" * 40)
    
    # Create CSV with same VINs but different data
    duplicate_vin_cars = [
        {
            "make": "BMW",
            "model": "X5 Updated",  # Changed model
            "number": "BMW001-NEW",  # Changed number
            "purchase_date": "2024-01-20",  # Changed date
            "vin": "WBAFR7C50BC123456",  # Same VIN as first car
            "image_url": "https://example.com/bmw-updated.jpg"
        },
        {
            "make": "Mercedes-Benz",  # Changed make
            "model": "C-Class AMG",  # Changed model
            "number": "MB002-UPDATED",  # Changed number
            "purchase_date": "2024-02-25",  # Changed date
            "vin": "WDDGF4HB1CA123789",  # Same VIN as second car
            "image_url": "https://example.com/mercedes-updated.jpg"
        }
    ]
    
    csv_content = tester.create_csv_content(duplicate_vin_cars)
    print(f"📄 CSV Content for duplicate VIN test:")
    print(csv_content)
    
    success, import_result = tester.test_csv_import(csv_content, "CSV Import with Duplicate VINs")
    
    if not success:
        print("❌ CRITICAL: CSV import with duplicate VINs failed")
        tester.cleanup()
        return 1
    
    # Verify import result structure
    print(f"\n🔍 VERIFYING IMPORT RESULT STRUCTURE")
    print("-" * 40)
    
    required_fields = ['success', 'imported_count', 'updated_count', 'errors', 'message']
    structure_valid = True
    
    for field in required_fields:
        if field in import_result:
            print(f"✅ Field '{field}' present: {import_result[field]}")
        else:
            print(f"❌ Missing required field: {field}")
            structure_valid = False
    
    if not structure_valid:
        print("❌ CRITICAL: Import result structure is invalid")
        tester.cleanup()
        return 1
    
    # Verify counts
    expected_imported = 0  # No new cars should be imported
    expected_updated = 2   # Two existing cars should be updated
    
    if import_result.get('imported_count') == expected_imported:
        print(f"✅ Imported count correct: {import_result['imported_count']}")
    else:
        print(f"❌ Imported count incorrect - expected: {expected_imported}, got: {import_result.get('imported_count')}")
        structure_valid = False
    
    if import_result.get('updated_count') == expected_updated:
        print(f"✅ Updated count correct: {import_result['updated_count']}")
    else:
        print(f"❌ Updated count incorrect - expected: {expected_updated}, got: {import_result.get('updated_count')}")
        structure_valid = False
    
    # Verify message includes both counts
    message = import_result.get('message', '')
    if 'updated' in message.lower() and str(expected_updated) in message:
        print(f"✅ Message includes updated count: {message}")
    else:
        print(f"❌ Message doesn't properly describe updates: {message}")
        structure_valid = False
    
    # Test 4: Verify Data Integrity After Updates
    print(f"\n🔍 VERIFYING DATA INTEGRITY AFTER UPDATES")
    print("-" * 40)
    
    # Verify first car was updated
    first_car_updated = tester.verify_car_updated(
        "WBAFR7C50BC123456",
        {
            "make": "BMW",
            "model": "X5 Updated",
            "number": "BMW001-NEW",
            "purchase_date": "2024-01-20",
            "image_url": "https://example.com/bmw-updated.jpg"
        }
    )
    
    # Verify second car was updated
    second_car_updated = tester.verify_car_updated(
        "WDDGF4HB1CA123789",
        {
            "make": "Mercedes-Benz",
            "model": "C-Class AMG", 
            "number": "MB002-UPDATED",
            "purchase_date": "2024-02-25",
            "image_url": "https://example.com/mercedes-updated.jpg"
        }
    )
    
    # Verify third car was NOT affected (should remain unchanged)
    third_car = tester.get_car_by_vin("WAUZZZ8K1DA123456")
    if third_car:
        if (third_car['make'] == 'Audi' and 
            third_car['model'] == 'A4' and 
            third_car['number'] == 'AUDI003'):
            print(f"✅ Third car (Audi) remained unchanged as expected")
            third_car_unchanged = True
        else:
            print(f"❌ Third car (Audi) was unexpectedly modified")
            third_car_unchanged = False
    else:
        print(f"❌ Third car (Audi) not found")
        third_car_unchanged = False
    
    # Test 5: Mixed CSV Import (New + Existing VINs)
    print(f"\n🔀 TESTING MIXED CSV IMPORT (NEW + EXISTING VINS)")
    print("-" * 40)
    
    mixed_cars = [
        {
            "make": "Toyota",
            "model": "Camry",
            "number": "TOY001",
            "purchase_date": "2024-04-15",
            "vin": "1HGBH41JXMN109186",  # New VIN
            "image_url": "https://example.com/toyota.jpg"
        },
        {
            "make": "Honda",
            "model": "Civic",
            "number": "HON002", 
            "purchase_date": "2024-05-20",
            "vin": "2HGFC2F59NH123456",  # New VIN
            "image_url": "https://example.com/honda.jpg"
        },
        {
            "make": "BMW",
            "model": "X5 Final Update",  # Update existing BMW again
            "number": "BMW001-FINAL",
            "purchase_date": "2024-01-25",
            "vin": "WBAFR7C50BC123456",  # Existing VIN
            "image_url": "https://example.com/bmw-final.jpg"
        }
    ]
    
    mixed_csv_content = tester.create_csv_content(mixed_cars)
    print(f"📄 CSV Content for mixed import test:")
    print(mixed_csv_content)
    
    success, mixed_import_result = tester.test_csv_import(mixed_csv_content, "Mixed CSV Import (New + Existing)")
    
    if not success:
        print("❌ CRITICAL: Mixed CSV import failed")
        tester.cleanup()
        return 1
    
    # Verify mixed import results
    expected_imported_mixed = 2  # Two new cars
    expected_updated_mixed = 1   # One existing car updated
    
    mixed_structure_valid = True
    
    if mixed_import_result.get('imported_count') == expected_imported_mixed:
        print(f"✅ Mixed import - Imported count correct: {mixed_import_result['imported_count']}")
    else:
        print(f"❌ Mixed import - Imported count incorrect - expected: {expected_imported_mixed}, got: {mixed_import_result.get('imported_count')}")
        mixed_structure_valid = False
    
    if mixed_import_result.get('updated_count') == expected_updated_mixed:
        print(f"✅ Mixed import - Updated count correct: {mixed_import_result['updated_count']}")
    else:
        print(f"❌ Mixed import - Updated count incorrect - expected: {expected_updated_mixed}, got: {mixed_import_result.get('updated_count')}")
        mixed_structure_valid = False
    
    # Test 6: Verify Final Data State
    print(f"\n🔍 VERIFYING FINAL DATA STATE")
    print("-" * 40)
    
    # Verify new cars were created
    toyota_car = tester.get_car_by_vin("1HGBH41JXMN109186")
    honda_car = tester.get_car_by_vin("2HGFC2F59NH123456")
    
    if toyota_car and toyota_car['make'] == 'Toyota':
        print(f"✅ New Toyota car created successfully")
    else:
        print(f"❌ New Toyota car not found or incorrect")
        mixed_structure_valid = False
    
    if honda_car and honda_car['make'] == 'Honda':
        print(f"✅ New Honda car created successfully")
    else:
        print(f"❌ New Honda car not found or incorrect")
        mixed_structure_valid = False
    
    # Verify BMW was updated again
    bmw_final_updated = tester.verify_car_updated(
        "WBAFR7C50BC123456",
        {
            "make": "BMW",
            "model": "X5 Final Update",
            "number": "BMW001-FINAL",
            "purchase_date": "2024-01-25",
            "image_url": "https://example.com/bmw-final.jpg"
        }
    )
    
    # Test 7: Error Handling - Invalid CSV
    print(f"\n⚠️  TESTING ERROR HANDLING")
    print("-" * 40)
    
    # Test with invalid CSV (missing required fields)
    invalid_csv = "make,model\nToyota,Prius\nHonda,Accord"
    
    success, error_result = tester.test_csv_import(invalid_csv, "Invalid CSV (Missing Required Fields)")
    
    # This should fail with 400 status, but our test expects 200, so we need to check the response
    if success and error_result.get('success') == False:
        print(f"✅ Invalid CSV properly rejected")
    elif not success:
        print(f"✅ Invalid CSV properly rejected with error status")
    else:
        print(f"❌ Invalid CSV was not properly rejected")
    
    # Clean up test data
    tester.cleanup()
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    # Summary of critical checks
    critical_checks = [
        ("Admin Authentication", success),
        ("Initial Cars Created", len(created_cars) == len(initial_cars)),
        ("Duplicate VIN Import", success and structure_valid),
        ("Data Integrity After Updates", first_car_updated and second_car_updated and third_car_unchanged),
        ("Mixed Import", success and mixed_structure_valid),
        ("Final Data State", bmw_final_updated and toyota_car and honda_car)
    ]
    
    print(f"\n🎯 Critical Checks Summary:")
    all_critical_passed = True
    for check_name, check_result in critical_checks:
        status = "✅ PASS" if check_result else "❌ FAIL"
        print(f"   {check_name}: {status}")
        if not check_result:
            all_critical_passed = False
    
    if all_critical_passed:
        print("\n🎉 All CSV import duplicate VIN tests passed!")
        print("✅ The system now properly handles duplicate VINs by updating existing records")
        print("✅ Import response includes both imported_count and updated_count")
        print("✅ Data integrity is maintained throughout the process")
        return 0
    else:
        failed_tests = tester.tests_run - tester.tests_passed
        print(f"\n❌ {failed_tests} tests failed or critical checks failed")
        return 1

def main():
    """Main test runner for CSV import duplicate VIN functionality"""
    print("🚗 Starting CSV Import Duplicate VIN Enhancement Tests")
    print("=" * 60)
    
    result = run_csv_import_duplicate_vin_tests()
    
    if result == 0:
        print("\n🎉 CSV Import Enhancement Testing Complete - All Tests Passed!")
        print("✅ The duplicate VIN issue has been successfully resolved")
        print("✅ Users can now import CSV files with existing VINs without errors")
        print("✅ Existing cars get updated instead of causing blocking errors")
    else:
        print("\n❌ CSV Import Enhancement Testing Failed")
        print("❌ Some issues remain with the duplicate VIN handling")
    
    return result

if __name__ == "__main__":
    sys.exit(main())