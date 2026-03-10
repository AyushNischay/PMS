
from flask import request, jsonify, session, Blueprint, current_app, render_template
from extensions import db
from models import Customer, Employee, Medicine, SalesTransaction, SalesDetail, InventoryUpdate, Supplier
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import os
from functools import wraps

bp = Blueprint('main', __name__)

# HTML Routes
@bp.route('/')
def home():
    return render_template('login.html')

@bp.route('/login')
def login_page():
    return render_template('login.html')

@bp.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')

@bp.route('/employee-dashboard')
def employee_dashboard_page():
    return render_template('employee_dashboard.html')

@bp.route('/inventory-page')
def inventory_page():
    return render_template('inventory.html')

@bp.route('/sales-page')
def sales_page():
    return render_template('sales.html')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Check header first (optional, for API clients)
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split()[1]
        
        # Check cookie if no header
        if not token:
            token = request.cookies.get('access_token')

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = {'id': data['user_id'], 'role': data['role'], 'type': data.get('type')}
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except Exception as e:
            return jsonify({'message': 'Token is invalid!', 'error': str(e)}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@bp.route('/auth/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role') # If provided, it's an employee
    
    if not name or not email or not password:
        return jsonify({'message': 'Missing fields'}), 400

    hashed_password = generate_password_hash(password, method='scrypt')

    if role:
        # Check if employee exists
        if Employee.query.filter_by(email=email).first():
             return jsonify({'message': 'Employee already exists'}), 409
        new_user = Employee(name=name, email=email, password=hashed_password, role=role, salary=data.get('salary', 0))
    else:
        # Check if customer exists
        if Customer.query.filter_by(email=email).first():
             return jsonify({'message': 'Email already registered'}), 409
        new_user = Customer(name=name, email=email, password=hashed_password, contact=data.get('contact'))

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Registration successful'}), 201

@bp.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Missing email or password'}), 400

    # Check Customer
    user = Customer.query.filter_by(email=email).first()
    user_type = 'customer'
    
    if not user:
        # Check Employee
        user = Employee.query.filter_by(email=email).first()
        user_type = 'employee'

    if not user or not check_password_hash(user.password, password):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    # Generate Token (Simple JWT)
    # Generate Token (Simple JWT)
    # Set shorter expiry for testing if needed, keeping 24h
    exp_time = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    token = jwt.encode({
        'user_id': user.id,
        'type': user_type,
        'role': user.role if user_type == 'employee' else 'customer',
        'exp': exp_time
    }, current_app.config['SECRET_KEY'], algorithm="HS256")

    response = jsonify({
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role if user_type == 'employee' else 'customer'
        },
        'exp': exp_time.timestamp() # Send expiry timestamp to client
    })
    
    # Set HttpOnly Cookie
    response.set_cookie('access_token', token, httponly=True, secure=False, samesite='Lax') # secure=True in production
    
    return response

@bp.route('/auth/logout', methods=['POST'])
def logout():
    response = jsonify({'message': 'Logged out successfully'})
    response.delete_cookie('access_token', path='/', samesite='Lax')
    return response
@bp.route('/auth/validate', methods=['GET'])
@token_required
def validate_token(current_user):
    return jsonify({'valid': True, 'user': current_user})

# Inventory Management
@bp.route('/inventory', methods=['GET'])
@token_required
def get_inventory(current_user):
    # Only Admin (Manager/Pharmacist) can view? 
    # Let's say anyone logged in can view
    medicines = Medicine.query.all()
    output = []
    for medicine in medicines:
        medicine_data = {}
        medicine_data['id'] = medicine.id
        medicine_data['name'] = medicine.name
        medicine_data['stock'] = medicine.stock
        medicine_data['expiry'] = str(medicine.expiry)
        medicine_data['price'] = medicine.price
        output.append(medicine_data)
    return jsonify({'medicines': output})

@bp.route('/inventory', methods=['POST'])
@token_required
def add_medicine(current_user):
    if current_user['role'] not in ['Admin', 'Manager']:
        return jsonify({'message': 'Permission denied'}), 403
        
    data = request.json
    new_medicine = Medicine(
        name=data['name'],
        stock=data['stock'],
        expiry=datetime.datetime.strptime(data['expiry'], '%Y-%m-%d').date() if data.get('expiry') else None,
        price=data['price']
    )
    db.session.add(new_medicine)
    db.session.commit() # Commit to get ID
    
    # Log initial stock
    if new_medicine.stock > 0:
        log = InventoryUpdate(medicine_id=new_medicine.id, quantity=new_medicine.stock, type='Initial')
        db.session.add(log)
        db.session.commit()

    return jsonify({'message': 'Medicine added successfully'}), 201

@bp.route('/inventory/<int:id>', methods=['PUT'])
@token_required
def update_medicine(current_user, id):
    if current_user['role'] not in ['Admin', 'Manager']:
        return jsonify({'message': 'Permission denied'}), 403

    medicine = Medicine.query.get(id)
    if not medicine:
        return jsonify({'message': 'Medicine not found'}), 404
        
    data = request.json
    old_stock = medicine.stock
    medicine.name = data.get('name', medicine.name)
    medicine.stock = data.get('stock', medicine.stock)
    
    if data.get('expiry'):
        medicine.expiry = datetime.datetime.strptime(data.get('expiry'), '%Y-%m-%d').date()
    medicine.price = data.get('price', medicine.price)
    
    # Log stock change if any (manual adjustment)
    if medicine.stock != old_stock:
        diff = medicine.stock - old_stock
        log = InventoryUpdate(medicine_id=medicine.id, quantity=abs(diff), type='Restock' if diff > 0 else 'Correction')
        db.session.add(log)
    
    db.session.commit()
    return jsonify({'message': 'Medicine updated successfully'})

@bp.route('/inventory/<int:id>', methods=['DELETE'])
@token_required
def delete_medicine(current_user, id):
    if current_user['role'] not in ['Admin', 'Manager']:
         return jsonify({'message': 'Permission denied'}), 403

    medicine = Medicine.query.get(id)
    if not medicine:
        return jsonify({'message': 'Medicine not found'}), 404
        
    db.session.delete(medicine)
    db.session.commit()
    return jsonify({'message': 'Medicine deleted successfully'})

@bp.route('/sales', methods=['GET'])
@token_required
def get_sales(current_user):
    if current_user['role'] not in ['Admin', 'Manager']:
        return jsonify({'message': 'Permission denied'}), 403

    from_date = request.args.get('from')
    to_date = request.args.get('to')

    query = SalesTransaction.query

    if from_date:
        try:
            from_dt = datetime.datetime.strptime(from_date, '%Y-%m-%d')
            query = query.filter(SalesTransaction.date >= from_dt)
        except ValueError:
            return jsonify({'message': 'Invalid from date format. Use YYYY-MM-DD'}), 400

    if to_date:
        try:
            # Include entire day for to_date
            to_dt = datetime.datetime.strptime(to_date, '%Y-%m-%d') + datetime.timedelta(days=1)
            query = query.filter(SalesTransaction.date < to_dt)
        except ValueError:
            return jsonify({'message': 'Invalid to date format. Use YYYY-MM-DD'}), 400

    sales = query.order_by(SalesTransaction.date.desc()).all()
    
    output = []
    for sale in sales:
        customer = Customer.query.get(sale.customer_id)
        employee_name = None
        if sale.employee_id:
            employee = Employee.query.get(sale.employee_id)
            if employee:
                employee_name = f"{employee.name} ({employee.role})"
                
        output.append({
            'id': sale.id,
            'date': sale.date.isoformat(),
            'total_amount': sale.total_amount,
            'customer_name': customer.name if customer else "Unknown",
            'customer_email': customer.email if customer else "Unknown",
            'employee_name': employee_name
        })

    return jsonify({'sales': output})

@bp.route('/sales', methods=['POST'])
@token_required
def create_sale(current_user):
    data = request.json
    items = data.get('items') # List of {medicine_id, quantity}
    
    cust_name = data.get('customer_name')
    cust_email = data.get('customer_email')
    cust_contact = data.get('customer_contact')

    if not items:
         return jsonify({'message': 'No items in sale'}), 400

    if not cust_email:
        return jsonify({'message': 'Customer email is required'}), 400

    try:
        # 1. Handle Customer (Find or Create)
        customer = Customer.query.filter_by(email=cust_email).first()
        if not customer:
            # Create a simple customer entry
            # Note: We need a placeholder password since it's nullable=False in models.py
            dummy_pass = generate_password_hash('pms_temp_123', method='scrypt')
            customer = Customer(
                name=cust_name or "Walk-in Customer",
                email=cust_email,
                password=dummy_pass,
                contact=cust_contact
            )
            db.session.add(customer)
            db.session.flush() # Get ID
        
        total_amount = 0
        employee_id = current_user['id'] if current_user.get('type') == 'employee' else None
        sale = SalesTransaction(customer_id=customer.id, employee_id=employee_id, date=datetime.datetime.utcnow())
        db.session.add(sale)
        db.session.flush() # Get sale ID

        for item in items:
            medicine = Medicine.query.get(item['medicine_id'])
            if not medicine:
                raise Exception(f"Medicine ID {item['medicine_id']} not found")
            
            if medicine.stock < item['quantity']:
                raise Exception(f"Insufficient stock for {medicine.name}")
            
            # Deduct stock
            medicine.stock -= item['quantity']
            
            # Add Sale Detail
            detail = SalesDetail(
                transaction_id=sale.id,
                medicine_id=medicine.id,
                quantity=item['quantity'],
                price=medicine.price
            )
            db.session.add(detail)
            
            # Log Inventory Update
            log = InventoryUpdate(
                medicine_id=medicine.id, 
                quantity=item['quantity'], 
                type='Sale'
            )
            db.session.add(log)
            
            total_amount += medicine.price * item['quantity']

        sale.total_amount = total_amount
        db.session.commit()
        return jsonify({'message': 'Sale created successfully', 'sale_id': sale.id, 'total': total_amount}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Transaction failed', 'error': str(e)}), 400

# Entity Management

# Customers
@bp.route('/customers', methods=['GET'])
@token_required
def get_customers(current_user):
    if current_user['role'] not in ['Admin', 'Manager']:
        return jsonify({'message': 'Permission denied'}), 403
    customers = Customer.query.all()
    output = []
    for c in customers:
        output.append({
            'id': c.id,
            'name': c.name,
            'email': c.email,
            'contact': c.contact
        })
    return jsonify(output)

@bp.route('/customers', methods=['POST'])
@token_required
def add_customer(current_user):
    # Depending on requirements, maybe only admin adds customers, or they register themselves (handled in /register)
    if current_user['role'] not in ['Admin', 'Manager']:
        return jsonify({'message': 'Permission denied'}), 403
    data = request.json
    hashed_password = generate_password_hash(data['password'], method='scrypt')
    new_customer = Customer(name=data['name'], email=data['email'], password=hashed_password, contact=data.get('contact'))
    db.session.add(new_customer)
    db.session.commit()
    return jsonify({'message': 'Customer created successfully'}), 201

@bp.route('/customers/<int:id>/history', methods=['GET'])
@token_required
def get_customer_history(current_user, id):
    # Allow if Admin/Manager OR if it's the customer requesting their own history
    if current_user['role'] not in ['Admin', 'Manager']:
        if current_user.get('type') != 'customer' or current_user['id'] != id:
            return jsonify({'message': 'Permission denied'}), 403
            
    customer = Customer.query.get(id)
    if not customer:
        return jsonify({'message': 'Customer not found'}), 404
        
    transactions = SalesTransaction.query.filter_by(customer_id=id).order_by(SalesTransaction.date.desc()).all()
    
    total_spent = 0
    txn_list = []
    
    for txn in transactions:
        total_spent += txn.total_amount
        items = []
        for detail in txn.details:
            medicine = Medicine.query.get(detail.medicine_id)
            items.append({
                'medicine': medicine.name if medicine else "Unknown Medicine",
                'quantity': detail.quantity,
                'price': detail.price
            })
            
        txn_list.append({
            'id': txn.id,
            'date': txn.date.isoformat(),
            'total_amount': txn.total_amount,
            'items': items
        })
        
    return jsonify({
        'customer_id': customer.id,
        'customer_name': customer.name,
        'total_spent': total_spent,
        'transactions': txn_list
    })

# Employees
@bp.route('/employees', methods=['GET'])
@token_required
def get_employees(current_user):
    if current_user['role'] != 'Admin':
        return jsonify({'message': 'Permission denied'}), 403
    employees = Employee.query.all()
    output = []
    for e in employees:
        output.append({
            'id': e.id,
            'name': e.name,
            'email': e.email,
            'role': e.role,
            'salary': e.salary
        })
    return jsonify(output)

@bp.route('/employees/<int:id>', methods=['PUT'])
@token_required
def update_employee(current_user, id):
    if current_user['role'] != 'Admin':
        return jsonify({'message': 'Permission denied'}), 403
    
    employee = Employee.query.get(id)
    if not employee:
        return jsonify({'message': 'Employee not found'}), 404
        
    data = request.json
    employee.name = data.get('name', employee.name)
    employee.email = data.get('email', employee.email)
    employee.role = data.get('role', employee.role)
    employee.salary = data.get('salary', employee.salary)
    
    if data.get('password'):
        employee.password = generate_password_hash(data['password'], method='scrypt')
        
    db.session.commit()
    return jsonify({'message': 'Employee updated successfully'})

@bp.route('/employees/<int:id>', methods=['DELETE'])
@token_required
def delete_employee(current_user, id):
    if current_user['role'] != 'Admin':
        return jsonify({'message': 'Permission denied'}), 403
        
    employee = Employee.query.get(id)
    if not employee:
        return jsonify({'message': 'Employee not found'}), 404
        
    db.session.delete(employee)
    db.session.commit()
    return jsonify({'message': 'Employee deleted successfully'})

# Suppliers
@bp.route('/suppliers', methods=['GET'])
@token_required
def get_suppliers(current_user):
    suppliers = Supplier.query.all()
    output = []
    for s in suppliers:
        output.append({'id': s.id, 'name': s.name, 'contact': s.contact})
    return jsonify(output)

@bp.route('/suppliers', methods=['POST'])
@token_required
def add_supplier(current_user):
    if current_user['role'] not in ['Admin', 'Manager']:
        return jsonify({'message': 'Permission denied'}), 403
    data = request.json
    new_supplier = Supplier(name=data['name'], contact=data.get('contact'))
    db.session.add(new_supplier)
    db.session.commit()
    return jsonify({'message': 'Supplier created successfully'}), 201

@bp.route('/suppliers/<int:id>', methods=['PUT'])
@token_required
def update_supplier(current_user, id):
    if current_user['role'] not in ['Admin', 'Manager']:
        return jsonify({'message': 'Permission denied'}), 403
        
    supplier = Supplier.query.get(id)
    if not supplier:
        return jsonify({'message': 'Supplier not found'}), 404
        
    data = request.json
    supplier.name = data.get('name', supplier.name)
    supplier.contact = data.get('contact', supplier.contact)
    
    db.session.commit()
    return jsonify({'message': 'Supplier updated successfully'})

@bp.route('/suppliers/<int:id>', methods=['DELETE'])
@token_required
def delete_supplier(current_user, id):
    if current_user['role'] not in ['Admin', 'Manager']:
        return jsonify({'message': 'Permission denied'}), 403
        
    supplier = Supplier.query.get(id)
    if not supplier:
        return jsonify({'message': 'Supplier not found'}), 404
        
    db.session.delete(supplier)
    db.session.commit()
    return jsonify({'message': 'Supplier deleted successfully'})