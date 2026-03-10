from flask import Blueprint, request, jsonify
from extensions import db
from models import Medicine, SalesTransaction, SalesDetail
from routes import token_required
from sqlalchemy import func
import datetime

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/low-stock', methods=['GET'])
@token_required
def get_low_stock(current_user):
    threshold = request.args.get('threshold', default=10, type=int)
    medicines = Medicine.query.filter(Medicine.stock <= threshold).all()
    
    output = []
    for med in medicines:
        output.append({
            'id': med.id,
            'name': med.name,
            'stock': med.stock,
            'price': med.price
        })
        
    return jsonify({
        'threshold': threshold,
        'count': len(output),
        'medicines': output
    })

@reports_bp.route('/expiring', methods=['GET'])
@token_required
def get_expiring(current_user):
    days = request.args.get('days', default=30, type=int)
    
    # Use timezone-aware UTC for current time comparison
    today = datetime.datetime.now(datetime.timezone.utc).date()
    target_date = today + datetime.timedelta(days=days)
    
    medicines = Medicine.query.filter(Medicine.expiry != None, Medicine.expiry <= target_date).all()
    
    output = []
    for med in medicines:
        output.append({
            'id': med.id,
            'name': med.name,
            'stock': med.stock,
            'expiry': med.expiry.isoformat(),
            'already_expired': med.expiry < today
        })
        
    return jsonify({
        'days_window': days,
        'count': len(output),
        'medicines': output
    })

@reports_bp.route('/sales', methods=['GET'])
@token_required
def get_sales_report(current_user):
    if current_user['role'] not in ['Admin', 'Manager']:
        return jsonify({'message': 'Permission denied'}), 403
        
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    
    if not from_date or not to_date:
        # Default to last 30 days
        to_dt = datetime.datetime.now(datetime.timezone.utc)
        from_dt = to_dt - datetime.timedelta(days=30)
    else:
        try:
            from_dt = datetime.datetime.strptime(from_date, '%Y-%m-%d')
            to_dt = datetime.datetime.strptime(to_date, '%Y-%m-%d') + datetime.timedelta(days=1)
        except ValueError:
            return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD'}), 400

    sales = db.session.query(
        func.date(SalesTransaction.date).label('date'),
        func.sum(SalesTransaction.total_amount).label('revenue'),
        func.count(SalesTransaction.id).label('transactions')
    ).filter(
        SalesTransaction.date >= from_dt,
        SalesTransaction.date < to_dt
    ).group_by(func.date(SalesTransaction.date)).all()
    
    total_revenue = sum(sale.revenue for sale in sales if sale.revenue)
    total_transactions = sum(sale.transactions for sale in sales if sale.transactions)
    
    breakdown = []
    for sale in sales:
        breakdown.append({
            'date': sale.date,
            'revenue': sale.revenue,
            'transactions': sale.transactions
        })
        
    return jsonify({
        'from': from_date or from_dt.strftime('%Y-%m-%d'),
        'to': to_date or (to_dt - datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
        'total_revenue': total_revenue,
        'total_transactions': total_transactions,
        'daily_breakdown': breakdown
    })

@reports_bp.route('/top-medicines', methods=['GET'])
@token_required
def get_top_medicines(current_user):
    limit = request.args.get('limit', default=10, type=int)
    
    top_meds = db.session.query(
        Medicine.id,
        Medicine.name,
        func.sum(SalesDetail.quantity).label('total_units_sold'),
        func.sum(SalesDetail.quantity * SalesDetail.price).label('total_revenue')
    ).join(SalesDetail, Medicine.id == SalesDetail.medicine_id)\
     .group_by(Medicine.id, Medicine.name)\
     .order_by(func.sum(SalesDetail.quantity).desc())\
     .limit(limit).all()
     
    output = []
    for med in top_meds:
        output.append({
            'medicine_id': med.id,
            'name': med.name,
            'total_units_sold': med.total_units_sold,
            'total_revenue': med.total_revenue
        })
        
    return jsonify({
        'top_medicines': output
    })
