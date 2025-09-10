#!/usr/bin/env python3
"""
Quick Delete Car Functionality Test
Test the delete car functionality to ensure the delete button is working properly.
"""

import requests
import json
import sys
from datetime import datetime

class DeleteCarTester:
    def __init__(self, base_url="https://dealership-tracker.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.auth_token = None
        self.auth_headers = {'Content-Type': 'application/json'}
        self.test_car_ids = []

    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def login_admin(self, username="admin", password="admin123"):
        """Login as admin and store JWT token"""
        self.log("🔐 Logging in as admin...")
        
        login_data = {
            "username": username,
            "password": password
        }
        
        try:
            url = f"{self.base_url}/auth/login"
            response = requests.post(url, json=login_data, headers={'Content-Type': 'application/json'})
            
            if response.status_code == 200:
                data = response.json()
                if 'access_token' in data:
                    self.auth_token = data['access_token']
                    self.auth_headers['Authorization'] = f'Bearer {self.auth_token}'
                    user_info = data.get('user', {})
                    self.log(f"✅ Admin login successful - User: {user_info.get('username')}, Role: {user_info.get('role')}")
                    return True, data
                else:
                    self.log("❌ No access token in response", "ERROR")
                    return False, {}
            else:
                self.log(f"❌ Login failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False, {}
                
        except Exception as e:
            self.log(f"❌ Login error: {str(e)}", "ERROR")
            return False, {}

    def get_all_cars(self):
        """Get current cars list"""
        self.log("📋 Getting current cars list...")
        
        try:
            url = f"{self.base_url}/cars"
            response = requests.get(url, headers=self.auth_headers)
            
            if response.status_code == 200:
                cars = response.json()
                self.log(f"✅ Found {len(cars)} cars in inventory")
                
                # Show first few cars for reference
                for i, car in enumerate(cars[:3]):
                    self.log(f"   {i+1}. {car.get('make', 'N/A')} {car.get('model', 'N/A')} (ID: {car.get('id', 'N/A')[:8]}...)")
                
                if len(cars) > 3:
                    self.log(f"   ... and {len(cars) - 3} more cars")
                
                return True, cars
            else:
                self.log(f"❌ Failed to get cars - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False, []
                
        except Exception as e:
            self.log(f"❌ Error getting cars: {str(e)}", "ERROR")
            return False, []

    def create_test_car(self):
        """Create a test car for deletion testing"""
        self.log("🚗 Creating test car for deletion testing...")
        
        test_car_data = {
            "make": "TestDelete",
            "model": "DeleteTest",
            "number": "DEL-TEST-001",
            "purchase_date": "2024-01-15",
            "vin": f"DELTEST{datetime.now().strftime('%H%M%S')}"
        }
        
        try:
            url = f"{self.base_url}/cars"
            response = requests.post(url, json=test_car_data, headers=self.auth_headers)
            
            if response.status_code == 200:
                car = response.json()
                car_id = car.get('id')
                if car_id:
                    self.test_car_ids.append(car_id)
                    self.log(f"✅ Test car created - ID: {car_id[:8]}..., Make: {car.get('make')}, Model: {car.get('model')}")
                    return True, car
                else:
                    self.log("❌ No car ID in response", "ERROR")
                    return False, {}
            else:
                self.log(f"❌ Failed to create test car - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False, {}
                
        except Exception as e:
            self.log(f"❌ Error creating test car: {str(e)}", "ERROR")
            return False, {}

    def delete_car(self, car_id):
        """Delete a specific car by ID"""
        self.log(f"🗑️  Attempting to delete car with ID: {car_id[:8]}...")
        
        try:
            url = f"{self.base_url}/cars/{car_id}"
            response = requests.delete(url, headers=self.auth_headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Car deletion successful - Response: {data}")
                return True, data
            else:
                self.log(f"❌ Car deletion failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False, {}
                
        except Exception as e:
            self.log(f"❌ Error deleting car: {str(e)}", "ERROR")
            return False, {}

    def verify_car_deleted(self, car_id):
        """Verify that the car is actually deleted from the database"""
        self.log(f"🔍 Verifying car {car_id[:8]}... is deleted from database...")
        
        try:
            # Try to get the specific car - should return 404
            url = f"{self.base_url}/cars/{car_id}"
            response = requests.get(url, headers=self.auth_headers)
            
            if response.status_code == 404:
                self.log("✅ Car successfully deleted - Returns 404 when queried")
                return True
            else:
                self.log(f"❌ Car still exists - Status: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying deletion: {str(e)}", "ERROR")
            return False

    def verify_car_not_in_list(self, car_id):
        """Verify that the deleted car doesn't appear in the cars list"""
        self.log(f"🔍 Verifying car {car_id[:8]}... is not in cars list...")
        
        success, cars = self.get_all_cars()
        if success:
            car_ids = [car.get('id') for car in cars]
            if car_id not in car_ids:
                self.log("✅ Deleted car is not in cars list")
                return True
            else:
                self.log("❌ Deleted car still appears in cars list", "ERROR")
                return False
        else:
            self.log("❌ Failed to get cars list for verification", "ERROR")
            return False

    def test_delete_without_auth(self, car_id):
        """Test delete car without authentication (should fail)"""
        self.log(f"🔒 Testing delete without authentication (should fail)...")
        
        try:
            url = f"{self.base_url}/cars/{car_id}"
            # Use headers without authorization
            headers = {'Content-Type': 'application/json'}
            response = requests.delete(url, headers=headers)
            
            if response.status_code == 403:
                self.log("✅ Delete without auth correctly failed with 403 Forbidden")
                return True
            elif response.status_code == 401:
                self.log("✅ Delete without auth correctly failed with 401 Unauthorized")
                return True
            else:
                self.log(f"❌ Delete without auth should fail but got status: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing unauthorized delete: {str(e)}", "ERROR")
            return False

    def test_delete_nonexistent_car(self):
        """Test deleting a non-existent car (should return 404)"""
        self.log("🔍 Testing delete of non-existent car (should return 404)...")
        
        fake_car_id = "nonexistent-car-id-12345"
        
        try:
            url = f"{self.base_url}/cars/{fake_car_id}"
            response = requests.delete(url, headers=self.auth_headers)
            
            if response.status_code == 404:
                self.log("✅ Delete non-existent car correctly returned 404")
                return True
            else:
                self.log(f"❌ Delete non-existent car should return 404 but got: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing non-existent car delete: {str(e)}", "ERROR")
            return False

    def run_delete_car_tests(self):
        """Run comprehensive delete car functionality tests"""
        self.log("🗑️  Starting Delete Car Functionality Tests")
        self.log("=" * 60)
        
        tests_passed = 0
        total_tests = 0
        
        # Test 1: Admin Login
        self.log("\n🔐 TEST 1: ADMIN AUTHENTICATION")
        self.log("-" * 40)
        
        total_tests += 1
        success, _ = self.login_admin("admin", "admin123")
        if success:
            tests_passed += 1
            self.log("✅ Test 1 PASSED: Admin authentication successful")
        else:
            self.log("❌ Test 1 FAILED: Admin authentication failed")
            return tests_passed, total_tests
        
        # Test 2: Get Current Cars List
        self.log("\n📋 TEST 2: GET CURRENT CARS LIST")
        self.log("-" * 40)
        
        total_tests += 1
        success, cars_before = self.get_all_cars()
        if success:
            tests_passed += 1
            self.log("✅ Test 2 PASSED: Successfully retrieved cars list")
            cars_count_before = len(cars_before)
        else:
            self.log("❌ Test 2 FAILED: Failed to get cars list")
            return tests_passed, total_tests
        
        # Test 3: Create Test Car (if no cars exist)
        self.log("\n🚗 TEST 3: CREATE TEST CAR FOR DELETION")
        self.log("-" * 40)
        
        total_tests += 1
        success, test_car = self.create_test_car()
        if success:
            tests_passed += 1
            test_car_id = test_car.get('id')
            self.log("✅ Test 3 PASSED: Test car created successfully")
        else:
            self.log("❌ Test 3 FAILED: Failed to create test car")
            return tests_passed, total_tests
        
        # Test 4: Test Admin Access Control (Delete without auth should fail)
        self.log("\n🔒 TEST 4: ADMIN ACCESS CONTROL")
        self.log("-" * 40)
        
        total_tests += 1
        success = self.test_delete_without_auth(test_car_id)
        if success:
            tests_passed += 1
            self.log("✅ Test 4 PASSED: Admin access control working correctly")
        else:
            self.log("❌ Test 4 FAILED: Admin access control not working")
        
        # Test 5: Delete Specific Car
        self.log("\n🗑️  TEST 5: DELETE SPECIFIC CAR")
        self.log("-" * 40)
        
        total_tests += 1
        success, _ = self.delete_car(test_car_id)
        if success:
            tests_passed += 1
            self.log("✅ Test 5 PASSED: Car deletion API call successful")
        else:
            self.log("❌ Test 5 FAILED: Car deletion API call failed")
            return tests_passed, total_tests
        
        # Test 6: Verify Car is Actually Deleted from Database
        self.log("\n🔍 TEST 6: VERIFY CAR DELETED FROM DATABASE")
        self.log("-" * 40)
        
        total_tests += 1
        success = self.verify_car_deleted(test_car_id)
        if success:
            tests_passed += 1
            self.log("✅ Test 6 PASSED: Car successfully deleted from database")
        else:
            self.log("❌ Test 6 FAILED: Car still exists in database")
        
        # Test 7: Verify Car Not in Cars List
        self.log("\n📋 TEST 7: VERIFY CAR NOT IN CARS LIST")
        self.log("-" * 40)
        
        total_tests += 1
        success = self.verify_car_not_in_list(test_car_id)
        if success:
            tests_passed += 1
            self.log("✅ Test 7 PASSED: Deleted car not in cars list")
        else:
            self.log("❌ Test 7 FAILED: Deleted car still in cars list")
        
        # Test 8: Verify Cars Count Decreased
        self.log("\n📊 TEST 8: VERIFY CARS COUNT DECREASED")
        self.log("-" * 40)
        
        total_tests += 1
        success, cars_after = self.get_all_cars()
        if success:
            cars_count_after = len(cars_after)
            # We created 1 test car and deleted it, so count should be same as before
            # But if there were existing cars and we deleted one, count should decrease
            expected_count = cars_count_before  # We created 1 and deleted 1
            
            if cars_count_after == expected_count:
                tests_passed += 1
                self.log(f"✅ Test 8 PASSED: Cars count correct - Before: {cars_count_before}, After: {cars_count_after}")
            else:
                self.log(f"❌ Test 8 FAILED: Cars count incorrect - Before: {cars_count_before}, After: {cars_count_after}, Expected: {expected_count}")
        else:
            self.log("❌ Test 8 FAILED: Failed to get cars list after deletion")
        
        # Test 9: Test Delete Non-existent Car
        self.log("\n🔍 TEST 9: DELETE NON-EXISTENT CAR")
        self.log("-" * 40)
        
        total_tests += 1
        success = self.test_delete_nonexistent_car()
        if success:
            tests_passed += 1
            self.log("✅ Test 9 PASSED: Non-existent car deletion handled correctly")
        else:
            self.log("❌ Test 9 FAILED: Non-existent car deletion not handled correctly")
        
        # Final Results
        self.log("\n" + "=" * 60)
        self.log(f"📊 FINAL RESULTS: {tests_passed}/{total_tests} tests passed")
        
        if tests_passed == total_tests:
            self.log("🎉 ALL DELETE CAR FUNCTIONALITY TESTS PASSED!")
            self.log("✅ Delete button functionality is working correctly")
            return tests_passed, total_tests
        else:
            failed_tests = total_tests - tests_passed
            self.log(f"❌ {failed_tests} tests failed")
            self.log("⚠️  Delete car functionality has issues that need to be addressed")
            return tests_passed, total_tests

def main():
    """Main function to run delete car tests"""
    tester = DeleteCarTester()
    
    try:
        tests_passed, total_tests = tester.run_delete_car_tests()
        
        # Return appropriate exit code
        if tests_passed == total_tests:
            print("\n✅ All delete car tests passed successfully!")
            return 0
        else:
            print(f"\n❌ {total_tests - tests_passed} delete car tests failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)