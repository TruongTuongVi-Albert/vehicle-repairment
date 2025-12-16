from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.dao import repair_dao, reception_dao, settings_dao, invoice_dao, component_dao
from app.models import ReceptionSlip, Car, RepairSlip, RepairDetail
from app import db
from datetime import datetime

cashier_bp = Blueprint('cashier', __name__)


def check_cashier():
    """Check if current user is cashier or admin"""
    role = session.get('role')
    return role in ['cashier', 'admin']


@cashier_bp.route('/')
def home():
    """Cashier home page"""
    if not check_cashier():
        return redirect(url_for('main.login'))
    
    # Get VAT rate
    vat_rate = settings_dao.get_setting_float('vat_rate', 10.0)

    # Get filter
    filter_status = request.args.get('filter')
    
    # Build query based on filter
    query = db.session.query(ReceptionSlip, Car, RepairSlip)\
        .join(Car, ReceptionSlip.car_id == Car.id)\
        .join(RepairSlip, ReceptionSlip.id == RepairSlip.reception_slip_id)
    
    if filter_status == 'completed':
        query = query.filter(ReceptionSlip.status == 'completed')
    elif filter_status == 'paid':
        query = query.filter(ReceptionSlip.status == 'paid')
    else:
        query = query.filter(ReceptionSlip.status.in_(['completed', 'paid']))
        
    results = query.order_by(RepairSlip.end_date.desc()).all()
    
    completed_slips = []
    for slip, car, repair in results:
        # Calculate total
        details = RepairDetail.query.filter_by(repair_slip_id=repair.id).all()
        subtotal = sum(d.price_at_time * d.quantity + d.labor_fee for d in details)
        
        completed_slips.append({
            'id': slip.id,
            'car_id': slip.car_id,
            'reception_date': slip.reception_date,
            'status': slip.status,
            'license_plate': car.license_plate,
            'owner_name': car.owner_name,
            'phone_number': car.phone_number,
            'repair_id': repair.id,
            'end_date': repair.end_date,
            'total_amount': float(subtotal) if subtotal else 0.0
        })

    # Get recent invoices
    recent_invoices_data = invoice_dao.get_recent_invoices(10)
    recent_invoices = []
    for inv, car in recent_invoices_data:
        recent_invoices.append({
            'id': inv.id,
            'repair_slip_id': inv.repair_slip_id,
            'total_amount': inv.total_amount,
            'vat_rate': inv.vat_rate,
            'created_at': inv.created_at,
            'license_plate': car.license_plate
        })
    
    return render_template('cashier/home.html', completed_slips=completed_slips, recent_invoices=recent_invoices, vat_rate=vat_rate, current_filter=filter_status)


@cashier_bp.route('/invoice/<int:repair_id>')
def invoice(repair_id):
    """View invoice details"""
    if not check_cashier():
        return redirect(url_for('main.login'))
    
    result = repair_dao.get_repair_by_id(repair_id)
    if not result:
        flash('Repair not found.')
        return redirect(url_for('cashier.home'))
    
    repair_slip, slip, car = result
    
    repair = {
        'repair_id': repair_slip.id,
        'license_plate': car.license_plate,
        'owner_name': car.owner_name,
        'phone_number': car.phone_number,
        'address': car.address,
        'vehicle_type': car.vehicle_type,
        'color': car.color,
        'reception_date': slip.reception_date,
        'status': slip.status
    }
    
    # Get items
    details = repair_dao.get_repair_details(repair_id)
    items = []
    for detail, component in details:
        items.append({
            'id': detail.id,
            'component_id': detail.component_id,
            'quantity': detail.quantity,
            'price_at_time': detail.price_at_time,
            'category': detail.category,
            'labor_fee': detail.labor_fee,
            'name': component.name if component else None
        })
    
    # Get VAT rate
    vat_rate = settings_dao.get_setting_float('vat_rate', 10.0)
    
    # Calculate totals
    subtotal = sum(item['price_at_time'] * item['quantity'] + item['labor_fee'] for item in items)
    vat_amount = float(subtotal) * (vat_rate / 100)
    total_amount = float(subtotal) + vat_amount
    
    today = datetime.now().strftime('%d/%m/%Y')
    
    return render_template('cashier/invoice.html', repair=repair, items=items, 
                           subtotal=subtotal, vat_rate=vat_rate, vat_amount=vat_amount, 
                           total_amount=total_amount, today=today)


@cashier_bp.route('/pay/<int:repair_id>', methods=['POST'])
def process_payment(repair_id):
    """Process payment and create invoice"""
    if not check_cashier():
        return redirect(url_for('main.login'))
    
    total_amount = float(request.form['total_amount'])
    
    # Get VAT rate
    vat_rate = settings_dao.get_setting_float('vat_rate', 10.0)
    
    # Create invoice
    invoice_dao.create_invoice(repair_id, session['user_id'], total_amount, vat_rate)
    
    # Update reception slip status to 'paid'
    repair = repair_dao.get_repair_only_by_id(repair_id)
    if repair:
        reception_dao.update_slip_status(repair.reception_slip_id, 'paid')
    
    flash('Payment processed successfully!')
    return redirect(url_for('cashier.home'))
