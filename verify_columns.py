from app import app
from extensions import db
from sqlalchemy import inspect

def check_sales_columns():
    with app.app_context():
        inspector = inspect(db.engine)
        columns = inspector.get_columns('sales_transactions')
        print("Columns in sales_transactions:")
        for col in columns:
            print(f" - {col['name']} ({col['type']})")

if __name__ == "__main__":
    check_sales_columns()
