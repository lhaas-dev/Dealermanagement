import requests
import json
import os
from datetime import datetime

def test_frontend_specific_issue():
    """Test the specific frontend filtering issue that might be causing imported cars not to appear"""
    print("🔍 FRONTEND-SPECIFIC ISSUE INVESTIGATION")
    print("=" * 60)
    print("Testing if frontend month/year filtering is causing imported cars to be hidden")
    
    base_url = "https://dealership-tracker.preview.emergentagent.com/api"
    
    # Login as admin
    login_data = {"username": "admin", "password": "admin123"}
    response = requests.post(f"{base_url}/auth/login", json=login_data)
    if response.status_code != 200:
        print("❌ CRITICAL: Admin login failed")
        return 1
    
    auth_token = response.json()['access_token']
    headers = {'Authorization': f'Bearer {auth_token}'}
    
    print("✅ Admin login successful")
    
    # Step 1: Import some cars and check if they appear with different filters
    print(f"\n📁 STEP 1: IMPORT TEST CARS")
    print("-" * 40)
    
    csv_content = """make,model,number,purchase_date,vin
TestBrand,TestModel1,TEST-001,2024-01-15,TEST123456789ABC
TestBrand,TestModel2,TEST-002,2024-02-20,TEST987654321DEF"""
    
    csv_file_path = "/app/test_frontend_issue.csv"
    with open(csv_file_path, 'w') as f:
        f.write(csv_content)
    
    # Import CSV
    with open(csv_file_path, 'rb') as f:
        files = {'file': ('test.csv', f, 'text/csv')}
        response = requests.post(f"{base_url}/cars/import-csv", files=files, headers=headers)
    
    if response.status_code != 200:
        print("❌ CSV Import failed")
        return 1
    
    import_result = response.json()
    print(f"✅ CSV Import successful: {import_result}")
    
    # Step 2: Test various query combinations that frontend might use
    print(f"\n🔍 STEP 2: TEST FRONTEND QUERY PATTERNS")
    print("-" * 40)
    
    current_date = datetime.now()
    
    # Test queries that might be used by frontend
    test_scenarios = [
        ("No parameters (default)", {}),
        ("Current month/year", {"month": current_date.month, "year": current_date.year}),
        ("Previous month", {"month": current_date.month - 1 if current_date.month > 1 else 12, 
                           "year": current_date.year if current_date.month > 1 else current_date.year - 1}),
        ("Status filter: absent", {"status": "absent"}),
        ("Status filter: present", {"status": "present"}),
        ("Search: TestBrand", {"search": "TestBrand"}),
        ("Complex filter", {"status": "absent", "month": current_date.month, "year": current_date.year}),
    ]
    
    for scenario_name, params in test_scenarios:
        response = requests.get(f"{base_url}/cars", headers=headers, params=params)
        
        if response.status_code == 200:
            results = response.json()
            test_cars = [car for car in results if car.get('make') == 'TestBrand']
            print(f"   ✅ {scenario_name}: {len(results)} total cars, {len(test_cars)} TestBrand cars")
            
            if len(test_cars) == 0 and scenario_name != "Status filter: present":
                print(f"   ⚠️  WARNING: TestBrand cars not found in '{scenario_name}' query!")
                # Show what cars were returned
                if len(results) > 0:
                    car_names = [f"{car.get('make')} {car.get('model')}" for car in results[:3]]
                    print(f"      Found cars: {car_names}")
                else:
                    print(f"      No cars returned at all")
        else:
            print(f"   ❌ {scenario_name}: Query failed")
    
    # Step 3: Check if there's a month/year mismatch
    print(f"\n🔍 STEP 3: DETAILED MONTH/YEAR ANALYSIS")
    print("-" * 40)
    
    # Get all cars and check their month/year values
    response = requests.get(f"{base_url}/cars", headers=headers)
    if response.status_code == 200:
        all_cars = response.json()
        test_cars = [car for car in all_cars if car.get('make') == 'TestBrand']
        print(f"Found {len(test_cars)} TestBrand cars:")
        
        for car in test_cars:
            car_month = car.get('current_month')
            car_year = car.get('current_year')
            expected_month = current_date.month
            expected_year = current_date.year
            
            print(f"   🚗 {car.get('make')} {car.get('model')}:")
            print(f"      Month/Year: {car_month}/{car_year}")
            print(f"      Expected: {expected_month}/{expected_year}")
            print(f"      Status: {car.get('status')}")
            print(f"      Archive Status: {car.get('archive_status')}")
            
            if car_month != expected_month or car_year != expected_year:
                print(f"      ❌ MISMATCH: Car has wrong month/year!")
            else:
                print(f"      ✅ Month/Year correct")
    
    # Step 4: Test available months endpoint
    print(f"\n📊 STEP 4: CHECK AVAILABLE MONTHS ENDPOINT")
    print("-" * 40)
    
    response = requests.get(f"{base_url}/cars/available-months", headers=headers)
    if response.status_code == 200:
        available_months = response.json()
        print(f"Available months returned: {len(available_months)}")
        for month_data in available_months:
            print(f"   📅 {month_data.get('month_name')} {month_data.get('year')}: {month_data.get('car_count')} cars")
        
        # Check if current month is in available months
        current_month_found = any(
            m.get('month') == current_date.month and m.get('year') == current_date.year 
            for m in available_months
        )
        
        if current_month_found:
            print(f"✅ Current month ({current_date.month}/{current_date.year}) found in available months")
        else:
            print(f"❌ Current month ({current_date.month}/{current_date.year}) NOT found in available months")
            print(f"   This could explain why frontend doesn't show imported cars!")
    
    # Clean up
    try:
        os.remove(csv_file_path)
    except:
        pass
    
    # Clean up test cars
    response = requests.get(f"{base_url}/cars", headers=headers)
    if response.status_code == 200:
        cleanup_cars = response.json()
        test_cars = [car for car in cleanup_cars if car.get('make') == 'TestBrand']
        for car in test_cars:
            if car.get('id'):
                requests.delete(f"{base_url}/cars/{car['id']}", headers=headers)
    
    print(f"\n📊 Frontend-specific investigation completed")
    return 0

if __name__ == "__main__":
    test_frontend_specific_issue()