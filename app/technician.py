from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.dao import repair_dao, reception_dao, component_dao
from app.models import ReceptionSlip, Car, RepairSlip
from app import db

technician_bp = Blueprint('technician', __name__)


def check_technician():
    """Check if current user is technician or admin"""
    role = session.get('role')
    return role in ['technician', 'admin']


def get_technician_data(filter_status=None):
    """Get slips for technician view"""
    slips = []
    user_id = session.get('user_id')
    
    # 1. Get Pending/Waiting slips (from reception_slips)
    if not filter_status or filter_status in ['quote', 'waiting']:
        results = db.session.query(ReceptionSlip, Car)\
            .join(Car, ReceptionSlip.car_id == Car.id)\
            .filter(ReceptionSlip.status.in_(['pending', 'waiting']))\
            .order_by(ReceptionSlip.reception_date.asc())\
            .all()
        
        for slip, car in results:
            slips.append({
                'id': slip.id,
                'repair_id': None,
                'status': slip.status,
                'license_plate': car.license_plate,
                'owner_name': car.owner_name,
                'vehicle_type': car.vehicle_type,
                'color': car.color,
                'date_display': slip.reception_date,
                'reception_date': slip.reception_date
            })

    # 2. Get Repairing/Completed slips (from repair_slips)
    if not filter_status or filter_status in ['repairing', 'complete']:
        db_status = 'completed' if filter_status == 'complete' else filter_status
        
        query = db.session.query(RepairSlip, ReceptionSlip, Car)\
            .join(ReceptionSlip, RepairSlip.reception_slip_id == ReceptionSlip.id)\
            .join(Car, ReceptionSlip.car_id == Car.id)\
            .filter(RepairSlip.technician_id == user_id)
        
        if db_status:
            query = query.filter(ReceptionSlip.status == db_status)
            
        results = query.order_by(RepairSlip.start_date.desc()).all()
        
        for repair, slip, car in results:
            slips.append({
                'id': slip.id,
                'repair_id': repair.id,
                'status': slip.status,
                'license_plate': car.license_plate,
                'owner_name': car.owner_name,
                'vehicle_type': car.vehicle_type,
                'color': car.color,
                'date_display': repair.start_date,
                'reception_date': slip.reception_date
            })
    
    # Sort by date if no filter
    if not filter_status:
        slips.sort(key=lambda x: x['date_display'] if x['date_display'] else x['reception_date'], reverse=True)
        
    return slips


@technician_bp.route('/')
def home():
    """Technician home page"""
    if not check_technician():
        return redirect(url_for('main.login'))
    
    filter_status = request.args.get('filter')
    slips = get_technician_data(filter_status)
    
    return render_template('technician/home.html', slips=slips, current_filter=filter_status)


@technician_bp.route('/start/<int:slip_id>', methods=['POST'])
def start_repair(slip_id):
    """Start a repair from reception slip"""
    if not check_technician():
        return redirect(url_for('main.login'))
    
    # Create repair slip
    repair = repair_dao.create_repair_slip(slip_id, session['user_id'])
    
    # Update reception slip status
    reception_dao.update_slip_status(slip_id, 'repairing')
    
    flash('Repair started. Please add items.')
    return redirect(url_for('technician.add_item_view', repair_id=repair.id))


@technician_bp.route('/detail/<int:slip_id>')
def view_detail(slip_id):
    """View repair detail"""
    if not check_technician():
        return redirect(url_for('main.login'))
    
    filter_status = request.args.get('filter')
    slips = get_technician_data(filter_status)
    
    # Get reception slip with car info
    result = reception_dao.get_slip_by_id(slip_id)
    if not result:
        flash('Slip not found.')
        return redirect(url_for('technician.home'))
    
    slip, car = result
    
    # Check if repair exists
    repair_slip = repair_dao.get_repair_by_reception_id(slip_id)
    
    repair = {
        'repair_id': repair_slip.id if repair_slip else None,
        'reception_id': slip.id,
        'status': slip.status,
        'description': slip.description,
        'license_plate': car.license_plate,
        'owner_name': car.owner_name,
        'phone_number': car.phone_number,
        'address': car.address,
        'vehicle_type': car.vehicle_type,
        'color': car.color
    }
    
    items = []
    if repair_slip:
        details = repair_dao.get_repair_details(repair_slip.id)
        for detail, component in details:
            items.append({
                'id': detail.id,
                'repair_slip_id': detail.repair_slip_id,
                'component_id': detail.component_id,
                'quantity': detail.quantity,
                'price_at_time': detail.price_at_time,
                'category': detail.category,
                'labor_fee': detail.labor_fee,
                'name': component.name if component else None,
                'price': component.current_price if component else None
            })
    
    components = component_dao.get_all_active()
    
    return render_template('technician/home.html', slips=slips, current_filter=filter_status, modal='detail', repair=repair, items=items, components=components)


@technician_bp.route('/repair/<int:repair_id>/add', methods=['GET'])
def add_item_view(repair_id):
    """View to add item to repair"""
    if not check_technician():
        return redirect(url_for('main.login'))
    
    slips = get_technician_data()
    
    result = repair_dao.get_repair_by_id(repair_id)
    if not result:
        flash('Repair not found.')
        return redirect(url_for('technician.home'))
    
    repair_slip, slip, car = result
    
    repair = {
        'repair_id': repair_slip.id,
        'reception_id': slip.id,
        'status': slip.status,
        'description': slip.description,
        'license_plate': car.license_plate,
        'owner_name': car.owner_name,
        'phone_number': car.phone_number,
        'address': car.address,
        'vehicle_type': car.vehicle_type,
        'color': car.color
    }
    
    details = repair_dao.get_repair_details(repair_id)
    items = []
    for detail, component in details:
        items.append({
            'id': detail.id,
            'repair_slip_id': detail.repair_slip_id,
            'component_id': detail.component_id,
            'quantity': detail.quantity,
            'price_at_time': detail.price_at_time,
            'category': detail.category,
            'labor_fee': detail.labor_fee,
            'name': component.name if component else None,
            'price': component.current_price if component else None
        })
    
    components = component_dao.get_all_active()
    
    return render_template('technician/home.html', slips=slips, modal='add_item', repair=repair, items=items, components=components)


@technician_bp.route('/repair/<int:repair_id>/edit/<int:item_id>', methods=['GET'])
def edit_item_view(repair_id, item_id):
    """View to edit item"""
    if not check_technician():
        return redirect(url_for('main.login'))
    
    slips = get_technician_data()
    
    result = repair_dao.get_repair_by_id(repair_id)
    if not result:
        flash('Repair not found.')
        return redirect(url_for('technician.home'))
    
    repair_slip, slip, car = result
    
    repair = {
        'repair_id': repair_slip.id,
        'reception_id': slip.id,
        'status': slip.status,
        'description': slip.description,
        'license_plate': car.license_plate,
        'owner_name': car.owner_name,
        'phone_number': car.phone_number,
        'address': car.address,
        'vehicle_type': car.vehicle_type,
        'color': car.color
    }
    
    details = repair_dao.get_repair_details(repair_id)
    items = []
    edit_item = None
    for detail, component in details:
        item_data = {
            'id': detail.id,
            'repair_slip_id': detail.repair_slip_id,
            'component_id': detail.component_id,
            'quantity': detail.quantity,
            'price_at_time': detail.price_at_time,
            'category': detail.category,
            'labor_fee': detail.labor_fee,
            'name': component.name if component else None,
            'price': component.current_price if component else None
        }
        items.append(item_data)
        if detail.id == item_id:
            edit_item = item_data
    
    components = component_dao.get_all_active()
    
    return render_template('technician/home.html', slips=slips, modal='add_item', repair=repair, items=items, components=components, edit_item=edit_item)


@technician_bp.route('/repair/<int:repair_id>/add_item', methods=['POST'])
def add_item(repair_id):
    """Add item to repair"""
    if not check_technician():
        return redirect(url_for('main.login'))
    
    component_id = request.form.get('component_id')
    quantity = int(request.form.get('quantity', 1))
    category = request.form.get('category', '')
    current_price = request.form.get('current_price', 0)
    
    try:
        current_price = float(current_price)
    except ValueError:
        current_price = 0
    
    labor_fee = 0
    if component_id:
        component = component_dao.get_component_by_id(int(component_id))
        if component:
            labor_fee = component.current_price
    else:
        component_id = None

    repair_dao.add_repair_detail(repair_id, component_id, quantity, current_price, category, labor_fee)
    flash('Item added.')
    
    return redirect(url_for('technician.view_detail', slip_id=repair_id))


@technician_bp.route('/item/update/<int:item_id>', methods=['POST'])
def update_item(item_id):
    """Update repair item"""
    if not check_technician():
        return redirect(url_for('main.login'))
    
    component_id = request.form.get('component_id')
    quantity = int(request.form.get('quantity', 1))
    category = request.form.get('category', '')
    current_price = request.form.get('current_price', 0)
    
    try:
        current_price = float(current_price)
    except ValueError:
        current_price = 0
    
    labor_fee = 0
    if component_id:
        component = component_dao.get_component_by_id(int(component_id))
        if component:
            labor_fee = component.current_price
    else:
        component_id = None
    
    detail = repair_dao.get_repair_detail_by_id(item_id)
    repair_id = detail.repair_slip_id if detail else None
    
    if repair_id:
        repair_dao.update_repair_detail(item_id, component_id, quantity, current_price, category, labor_fee)
        flash('Item updated.')
        return redirect(url_for('technician.view_detail', slip_id=repair_id))
    
    return redirect(url_for('technician.home'))


@technician_bp.route('/item/delete/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    """Delete repair item"""
    if not check_technician():
        return redirect(url_for('main.login'))
    
    repair_id = repair_dao.delete_repair_detail(item_id)
    
    if repair_id:
        flash('Item deleted.')
        return redirect(url_for('technician.view_detail', slip_id=repair_id))
    
    return redirect(url_for('technician.home'))


@technician_bp.route('/repair/<int:repair_id>/finish', methods=['POST'])
def finish_repair(repair_id):
    """Finish repair and send to cashier"""
    if not check_technician():
        return redirect(url_for('main.login'))
    
    repair = repair_dao.get_repair_only_by_id(repair_id)
    if repair:
        reception_dao.update_slip_status(repair.reception_slip_id, 'completed')
        repair_dao.finish_repair(repair_id)
    
    flash('Repair finished. Sent to Cashier.')
    return redirect(url_for('technician.home'))
