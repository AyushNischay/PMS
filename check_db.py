from app import app
from extensions import db
from sqlalchemy import inspect
from models import Medicine, Customer, Employee, Supplier, SalesTransaction, SalesDetail, InventoryUpdate

def check_connection():
    print("Checking database connection...")
    try:
        with app.app_context():
            # Get the database URI from config
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            print(f"Database URI: {db_uri}")

            # Inspect the database
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if not tables:
                print("Connected, but NO tables found.")
            else:
                print(f"Successfully connected. Found {len(tables)} tables:")
                for table in tables:
                    print(f" - {table}")

            # Optional: Check row counts for a few key tables
            print("\nRow counts:")
            try:
                medicine_count = Medicine.query.count()
                print(f" - Medicines: {medicine_count}")
            except Exception as e:
                print(f" - Medicines: Error querying table ({e})")

            try:
                customer_count = Customer.query.count()
                print(f" - Customers: {customer_count}")
            except Exception as e:
                 print(f" - Customers: Error querying table ({e})")

    except Exception as e:
        print(f"CRITICAL ERROR connecting to database: {e}")

if __name__ == "__main__":
    check_connection()
