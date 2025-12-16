from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.dao import reception_dao, car_dao, settings_dao
from datetime import datetime

reception_bp = Blueprint('reception', __name__)


def check_reception():
    """Check if current user is reception or admin"""
    role = session.get('role')
    return role in ['reception', 'admin']


def get_reception_data():
    """Get common reception data for templates"""
    max_cars = settings_dao.get_setting_int('max_cars_per_day', 30)
    cars_today_count = reception_dao.count_today_slips()
    slips_data = reception_dao.get_all_slips()
    
    # Convert to list of dicts for template compatibility
    slips = []
    for slip, car in slips_data:
        slips.append({
            'id': slip.id,
            'car_id': slip.car_id,
            'reception_date': slip.reception_date,
            'status': slip.status,
            'description': slip.description,
            'license_plate': car.license_plate,
            'owner_name': car.owner_name,
            'phone_number': car.phone_number,
            'vehicle_type': car.vehicle_type,
            'address': car.address,
            'email': car.email,
            'color': car.color
        })
    
    return max_cars, cars_today_count, slips


@reception_bp.route('/')
def home():
    """Reception home page"""
    if not check_reception():
        return redirect(url_for('main.login'))
    
    max_cars, cars_today_count, slips = get_reception_data()
    
    return render_template('reception/home.html', slips=slips, cars_today_count=cars_today_count, max_cars=max_cars)


@reception_bp.route('/add', methods=['GET', 'POST'])
def add_car():
    """Add or edit a reception slip"""
    if not check_reception():
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        # Check max cars limit
        max_cars = settings_dao.get_setting_int('max_cars_per_day', 30)
        current_count = reception_dao.count_today_slips()
        
        if current_count >= max_cars:
            flash(f'Daily limit of {max_cars} cars reached. Cannot receive more cars today.')
            return redirect(url_for('reception.home'))
            
        # Process form
        license_plate = request.form['license_plate']
        owner_name = request.form['owner_name']
        phone = request.form['phone_number']
        address = request.form['address']
        email = request.form.get('email', '')
        description = request.form.get('description', '')
        vehicle_type = request.form.get('vehicle_type', 'Car')
        color = request.form.get('color', '')
        status = request.form.get('status', 'pending')
        
        # Create or update car
        car = car_dao.create_or_update_car(license_plate, owner_name, phone, address, email, vehicle_type, color)
        
        # Check if updating existing slip
        slip_id = request.args.get('slip_id')
        if slip_id:
            reception_dao.update_slip(int(slip_id), car.id, description, status)
            flash('Reception slip updated successfully!')
        else:
            reception_dao.create_slip(car.id, description, status)
            flash('Car received successfully!')
            
        return redirect(url_for('reception.home'))
    
    # GET request - show modal
    max_cars, cars_today_count, slips = get_reception_data()
    
    # Check if editing
    slip_id = request.args.get('slip_id')
    slip = None
    if slip_id:
        result = reception_dao.get_slip_by_id(int(slip_id))
        if result:
            s, car = result
            slip = {
                'id': s.id,
                'car_id': s.car_id,
                'reception_date': s.reception_date,
                'status': s.status,
                'description': s.description,
                'license_plate': car.license_plate,
                'owner_name': car.owner_name,
                'phone_number': car.phone_number,
                'vehicle_type': car.vehicle_type,
                'address': car.address,
                'email': car.email,
                'color': car.color
            }
    
    now_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('reception/home.html', slips=slips, cars_today_count=cars_today_count, max_cars=max_cars, modal='add', slip=slip, now_date=now_date)


@reception_bp.route('/detail/<int:slip_id>')
def detail(slip_id):
    """View reception slip details"""
    if not check_reception():
        return redirect(url_for('main.login'))
    
    max_cars, cars_today_count, slips = get_reception_data()
    
    result = reception_dao.get_slip_by_id(slip_id)
    if not result:
        flash('Reception slip not found.')
        return redirect(url_for('reception.home'))
    
    s, car = result
    slip = {
        'id': s.id,
        'car_id': s.car_id,
        'reception_date': s.reception_date,
        'status': s.status,
        'description': s.description,
        'license_plate': car.license_plate,
        'owner_name': car.owner_name,
        'phone_number': car.phone_number,
        'vehicle_type': car.vehicle_type,
        'address': car.address,
        'email': car.email,
        'color': car.color
    }
        
    return render_template('reception/home.html', slips=slips, cars_today_count=cars_today_count, max_cars=max_cars, modal='detail', slip=slip)
