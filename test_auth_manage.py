import requests
import json

import time

BASE_URL = 'http://127.0.0.1:5000'

def test_auth_and_management():
    session = requests.Session()
    
    # 1. Test Sign Up (Customer)
    print("Testing Sign Up (Customer)...")
    customer_data = {
        "name": "New Customer",
        "email": f"cust_{int(time.time())}@test.com",
        "password": "password123"
    }
    resp = session.post(f"{BASE_URL}/auth/register", json=customer_data)
    print(f"Register Result: {resp.status_code}, {resp.json()}")
    assert resp.status_code == 201

    # 2. Test Login (Customer) - Should redirect to employee-dashboard (or stay customer)
    # Note: In our implementation, customers get the same simplified dashboard as employees for now
    print("\nTesting Login (Customer)...")
    resp = session.post(f"{BASE_URL}/auth/login", json={"email": customer_data["email"], "password": customer_data["password"]})
    print(f"Login Result: {resp.status_code}, Role: {resp.json()['user']['role']}")
    assert resp.status_code == 200

    # 3. Test Admin Employee Management
    # Login as Admin first (using credentials from previous runs or creating one)
    print("\nRegistering/Logging in Admin...")
    admin_data = {
        "name": "Super Admin",
        "email": "admin@test.com",
        "password": "adminpassword",
        "role": "Admin"
    }
    session.post(f"{BASE_URL}/auth/register", json=admin_data) # Attempt register
    resp = session.post(f"{BASE_URL}/auth/login", json={"email": "admin@test.com", "password": "adminpassword"})
    
    # 4. Create Employee (via Register with role)
    print("\nTesting Admin Creating Employee...")
    new_emp_email = f"emp_{int(time.time())}@test.com"
    emp_data = {
        "name": "Test Employee",
        "email": new_emp_email,
        "password": "emppassword",
        "role": "Pharmacist",
        "salary": 3000
    }
    # Using register for simplicity as it handles both
    resp = session.post(f"{BASE_URL}/auth/register", json=emp_data)
    print(f"Create Employee Result: {resp.status_code}")
    
    # 5. List Employees
    resp = session.get(f"{BASE_URL}/employees")
    employees = resp.json()
    test_emp = next(e for e in employees if e['email'] == new_emp_email)
    print(f"Found Employee: {test_emp['name']}, ID: {test_emp['id']}")

    # 6. Update Employee
    print("\nTesting Update Employee...")
    resp = session.put(f"{BASE_URL}/employees/{test_emp['id']}", json={"name": "Updated Employee", "salary": 3500})
    print(f"Update Result: {resp.status_code}, {resp.json()}")
    assert resp.status_code == 200

    # 7. Delete Employee
    print("\nTesting Delete Employee...")
    resp = session.delete(f"{BASE_URL}/employees/{test_emp['id']}")
    print(f"Delete Result: {resp.status_code}, {resp.json()}")
    assert resp.status_code == 200

    print("\nAll automated tests passed!")

if __name__ == '__main__':
    try:
        test_auth_and_management()
    except Exception as e:
        print(f"Test failed: {e}")
