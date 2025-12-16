from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.dao import settings_dao, component_dao, invoice_dao, reception_dao, repair_dao
from app.models import ReceptionSlip, Car, RepairDetail
from app import db
from sqlalchemy import func, extract
from datetime import datetime
import calendar
import random

admin_bp = Blueprint('admin', __name__)


def check_admin():
    """Check if current user is admin"""
    return session.get('role') == 'admin'


@admin_bp.route('/dashboard')
def dashboard():
    """Admin dashboard with statistics"""
    if not check_admin():
        return redirect(url_for('main.login'))
    
    # Filter params
    now = datetime.now()
    filter_day = request.args.get('day')
    filter_month = request.args.get('month', now.month)
    filter_year = request.args.get('year', now.year)
    
    try:
        filter_month = int(filter_month)
        filter_year = int(filter_year)
        if filter_day:
            filter_day = int(filter_day)
    except ValueError:
        filter_month = now.month
        filter_year = now.year
        filter_day = None

    # 1. Revenue Data
    daily_revenue = invoice_dao.get_revenue_by_month(filter_month, filter_year)
    total_revenue = sum(daily_revenue.values())
    
    # Fill missing days with 0
    _, num_days = calendar.monthrange(filter_year, filter_month)
    for day in range(1, num_days + 1):
        if day not in daily_revenue:
            daily_revenue[day] = 0
    
    # Format for chart
    max_revenue = max(daily_revenue.values()) if daily_revenue.values() else 0
    chart_data = [{'label': d, 'value': v, 'percent': (v/max_revenue*100 if max_revenue else 0)} 
                  for d, v in sorted(daily_revenue.items())]

    # 2. Vehicle Types Ratio
    vehicle_counts = db.session.query(
        Car.vehicle_type, func.count(Car.id).label('count')
    ).join(ReceptionSlip, ReceptionSlip.car_id == Car.id)\
     .filter(
        extract('month', ReceptionSlip.reception_date) == filter_month,
        extract('year', ReceptionSlip.reception_date) == filter_year
    ).group_by(Car.vehicle_type).all()
    
    stats = {}
    pie_stops = {}
    total_vehicles = 0
    
    for v_type, count in vehicle_counts:
        stats[v_type] = count
        total_vehicles += count

    prev_v_type = None
    for v_type in stats:
        if pie_stops.get(prev_v_type):
            pie_stops[v_type] = {
                'from': pie_stops[prev_v_type]['to'],
                'to': pie_stops[prev_v_type]['to'] + stats[v_type] / total_vehicles * 360
            }
        else:
            pie_stops[v_type] = {
                'from': 0,
                'to': stats[v_type] / total_vehicles * 360 if total_vehicles else 0
            }
        prev_v_type = v_type

    # Generate random colors for each vehicle type
    colors = {}
    for v_type in stats:
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        colors[v_type] = f'rgb({r},{g},{b})'

    # 2.5 Category Stats (for Horizontal Bar Chart)
    from app.models import RepairSlip
    category_counts = db.session.query(
        RepairDetail.category, func.count(RepairDetail.id).label('count')
    ).join(RepairSlip, RepairDetail.repair_slip_id == RepairSlip.id)\
     .join(ReceptionSlip, RepairSlip.reception_slip_id == ReceptionSlip.id)\
     .filter(
        extract('month', ReceptionSlip.reception_date) == filter_month,
        extract('year', ReceptionSlip.reception_date) == filter_year
    ).group_by(RepairDetail.category).all()
    
    category_stats = {}
    total_items = 0
    
    for cat, count in category_counts:
        cat_name = cat if cat else "Uncategorized"
        category_stats[cat_name] = count
        total_items += count
        
    # Generate colors for categories
    category_colors = {}
    for cat in category_stats:
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        category_colors[cat] = f'rgb({r},{g},{b})'

    # 3. Settings & Components
    settings = settings_dao.get_all_settings()
    components = component_dao.get_all_active()
    
    # 4. Handle Edit Component
    edit_component = None
    edit_id = request.args.get('edit_id')
    if edit_id:
        edit_component = component_dao.get_component_by_id(int(edit_id))

    return render_template('admin/dashboard.html', 
                           settings=settings, 
                           components=components,
                           chart_data=chart_data,
                           stats=stats,
                           total_revenue=total_revenue,
                           pie_stops=pie_stops,
                           colors=colors,
                           total_vehicles=total_vehicles,
                           category_stats=category_stats,
                           category_colors=category_colors,
                           total_items=total_items,
                           edit_component=edit_component,
                           filter={'day': filter_day, 'month': filter_month, 'year': filter_year})


@admin_bp.route('/settings', methods=['POST'])
def update_settings():
    """Update system settings"""
    if not check_admin():
        return redirect(url_for('main.login'))
    
    max_cars = request.form['max_cars']
    vat_rate = request.form['vat_rate']
    
    settings_dao.set_setting('max_cars_per_day', max_cars)
    settings_dao.set_setting('vat_rate', vat_rate)
    
    flash('Settings updated.')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/component/add', methods=['POST'])
def add_component():
    """Add a new component"""
    if not check_admin():
        return redirect(url_for('main.login'))
    
    name = request.form['name']
    price = float(request.form['price'])
    stock = int(request.form.get('stock', 0))
    
    component_dao.add_component(name, price, stock)
    
    flash('Component added.')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/component/update/<int:component_id>', methods=['POST'])
def update_component(component_id):
    """Update a component"""
    if not check_admin():
        return redirect(url_for('main.login'))
    
    name = request.form['name']
    price = float(request.form['price'])
    stock = int(request.form.get('stock', 0))
    
    component_dao.update_component(component_id, name, price, stock)
    
    flash('Component updated.')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/component/delete/<int:component_id>', methods=['POST'])
def delete_component(component_id):
    """Soft delete a component"""
    if not check_admin():
        return redirect(url_for('main.login'))
    
    if component_dao.soft_delete_component(component_id):
        flash('Component deleted.')
    else:
        flash('Error: Cannot delete component.')
        
    return redirect(url_for('admin.dashboard'))
