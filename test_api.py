
import requests
import json

BASE_URL = 'http://127.0.0.1:5000'

def test_flow():
    session = requests.Session()
    
    # 1. Register Admin (if not exists)
    # Since we can't easily check if exists without login, we try to login first.
    # But wait, my register endpoint is /auth/register
    
    # Let's try to register a fresh admin
    admin_data = {
        "name": "Admin User",
        "email": "admin@test.com",
        "password": "adminpassword",
        "role": "Admin",
        "salary": 50000
    }
    
    print("Registering Admin...")
    resp = session.post(f"{BASE_URL}/auth/register", json=admin_data)
    print(f"Register Status: {resp.status_code}, Body: {resp.text}")
    
    # 2. Login Admin
    print("Logging in Admin...")
    login_data = {
        "email": "admin@test.com",
        "password": "adminpassword"
    }
    resp = session.post(f"{BASE_URL}/auth/login", json=login_data)
    if resp.status_code != 200:
        print("Login failed")
        return
    
    token = resp.json()['token']
    headers = {'Authorization': f'Bearer {token}'}
    print("Login successful.")

    # 3. Add Supplier
    print("Adding Supplier...")
    supplier_data = {"name": "Test Supplier", "contact": "1234567890"}
    resp = session.post(f"{BASE_URL}/suppliers", json=supplier_data, headers=headers)
    print(f"Add Supplier Status: {resp.status_code}")

    # 4. Add Medicine
    print("Adding Medicine...")
    medicine_data = {
        "name": "Paracetamol",
        "stock": 100,
        "expiry": "2025-12-31",
        "price": 10.0
    }
    resp = session.post(f"{BASE_URL}/inventory", json=medicine_data, headers=headers)
    print(f"Add Medicine Status: {resp.status_code}")
    
    # Get Medicine ID
    resp = session.get(f"{BASE_URL}/inventory", headers=headers)
    medicines = resp.json()['medicines']
    med_id = medicines[0]['id']
    print(f"Medicine ID: {med_id}")
    
    # 5. Create Sale
    print("Creating Sale...")
    sale_data = {
        "customer_id": None, # Walk-in
        "items": [
            {"medicine_id": med_id, "quantity": 2}
        ]
    }
    resp = session.post(f"{BASE_URL}/sales", json=sale_data, headers=headers)
    print(f"Sale Status: {resp.status_code}, Body: {resp.text}")
    
    # 6. Verify Stock Update
    resp = session.get(f"{BASE_URL}/inventory", headers=headers)
    medicines = resp.json()['medicines']
    new_stock = medicines[0]['stock']
    print(f"New Stock: {new_stock} (Expected 98)")

if __name__ == '__main__':
    test_flow()
