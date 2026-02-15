# PMS Project Roadmap & Checklist

This todo list is derived from the PRD, Design Document, and Tech Stack.

## 1. Project Initialization & Database Setup

- [ ] **Infrastructure Setup**
  - [ ] Initialize Git repository
  - [ ] Set up Python virtual environment (`venv`)
  - [ ] Install dependencies (Flask/FastAPI, SQLAlchemy/PyMySQL, Flask-CORS)
- [ ] **Database schema (MySQL)**
  - [ ] Create `Medicines` table (ID, Name, Stock, Expiry, Price)
  - [ ] Create `Customers` table (ID, Name, Email, Password, Contact)
  - [ ] Create `Employees` table (ID, Name, Role, Salary)
  - [ ] Create `Suppliers` table (ID, Name, Contact)
  - [ ] Create `SalesTransactions` & `SalesDetails` tables
  - [ ] Create `InventoryUpdates` table
  - [ ] Implement database triggers for stock validation

## 2. Backend Development (Python API)

- [ ] **Authentication Module**
  - [ ] Implement SHA-256 password hashing
  - [ ] Create Login/Logout endpoints (Admin & Customer)
  - [ ] Implement role-based access control (RBAC)
- [ ] **Inventory Management**
  - [ ] CRUD endpoints for Medicines
  - [ ] Low-stock & Expiry alert logic
  - [ ] Auto-update stock on sales/restocking
- [ ] **Sales & Billing**
  - [ ] Create Transaction endpoint
  - [ ] Stock availability check before sale
  - [ ] Transaction logging (ACID compliance)
- [ ] **Entity Management**
  - [ ] CRUD endpoints for Customers, Employees, and Suppliers

## 3. Frontend Development (HTML/CSS/JS)

- [ ] **Core UI System**
  - [ ] Setup `index.css` with modern design tokens (vibrant colors, glassmorphism)
  - [ ] Create Fixed sidebar navigation
  - [ ] Implement responsive grid/table layout
- [ ] **Pages & Components**
  - [ ] **Dashboard**: Key metrics (Total Sales, Low Stock count)
  - [ ] **Inventory**: Sortable medicine table with search
  - [ ] **Sales**: Form for creating bills with multi-medicine selection
  - [ ] **Reports**: Visualized summaries and alert lists
- [ ] **Interactions**
  - [ ] Implement AJAX/fetch for all CRUD operations
  - [ ] Add loading animations and color-coded alerts
  - [ ] Keyboard shortcuts for common actions

## 4. Reporting & Analytics

- [ ] **Data Aggregation**
  - [ ] Sales by date/period endpoint
  - [ ] Top-selling medicines logic
- [ ] **User Summaries**
  - [ ] Customer purchase history view

## 5. Verification & Testing

- [ ] **Testing**
  - [ ] Manual DB integrity checks
  - [ ] Browser testing (Chrome/Firefox)
  - [ ] Validate stock accuracy (>95%)
  - [ ] Verify billing time (<1 minute)
