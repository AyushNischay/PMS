import requests
import json
import uuid

BASE_URL = 'http://127.0.0.1:5000'

def verify():
    session = requests.Session()
    unique_suffix = str(uuid.uuid4())[:8]
    
    # 1. Test Employee Registration
    emp_email = f"emp_{unique_suffix}@test.com"
    print(f"Testing Employee Registration ({emp_email})...")
    reg_data = {
        "name": "Test Pharmacist",
        "email": emp_email,
        "password": "password123",
        "role": "Pharmacist"
    }
    resp = session.post(f"{BASE_URL}/auth/register", json=reg_data)
    print(f"Register Status: {resp.status_code}, Body: {resp.text}")
    assert resp.status_code == 201

    # 2. Login as Employee
    print("Testing Login...")
    login_data = {"email": emp_email, "password": "password123"}
    resp = session.post(f"{BASE_URL}/auth/login", json=login_data)
    assert resp.status_code == 200
    print("Login Successful.")

    # 3. Test Sale with New Customer
    cust_email = f"cust_{unique_suffix}@test.com"
    print(f"Testing Sale with New Customer ({cust_email})...")
    
    # Need to get a medicine ID first
    inv_resp = session.get(f"{BASE_URL}/inventory")
    medicines = inv_resp.json().get('medicines', [])
    if not medicines:
        print("No medicines found, skipping sale test.")
        return
    
    med_id = medicines[0]['id']
    
    sale_data = {
        "customer_name": "New Customer Test",
        "customer_email": cust_email,
        "customer_contact": "9998887776",
        "items": [{"medicine_id": med_id, "quantity": 1}]
    }
    
    resp = session.post(f"{BASE_URL}/sales", json=sale_data)
    print(f"Sale Status: {resp.status_code}, Body: {resp.text}")
    assert resp.status_code == 201
    print("Sale Successful.")

    print("\nVERIFICATION COMPLETE: Everything working as expected.")

if __name__ == "__main__":
    try:
        verify()
    except Exception as e:
        print(f"VERIFICATION FAILED: {e}")
