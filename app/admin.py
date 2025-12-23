from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.dao import settings_dao, component_dao, invoice_dao, reception_dao, repair_dao
from app.models import ReceptionSlip, Car, RepairDetail, Component, RepairSlip
from app import db
from app.dao.component_dao import ComponentDAO
from app.dao.settings_dao import SettingsDAO
from sqlalchemy import func, extract
from datetime import datetime, timedelta
import calendar
import random

admin_bp = Blueprint('admin', __name__)


def check_admin():
    """Check if current user is admin"""
    return session.get('role') == 'admin'


@admin_bp.route('/dashboard')
def dashboard():
    if not check_admin():
        return redirect(url_for('main.login'))

    # Filter params
    now = datetime.now()
    filter_day = request.args.get('day', '')
    filter_month = request.args.get('month', now.month)
    filter_year = request.args.get('year', now.year)

    try:
        filter_month = int(filter_month)
        filter_year = int(filter_year)
        if filter_day:
            filter_day = int(filter_day)
        else:
            filter_day = None
    except ValueError:
        filter_month = now.month
        filter_year = now.year
        filter_day = None

    # ============================================
    # 1. REVENUE DATA - Dữ liệu thật từ Invoices
    # ============================================
    daily_revenue = invoice_dao.get_revenue_by_month(filter_month, filter_year)
    total_revenue = sum(daily_revenue.values())

    # Fill missing days with 0
    _, num_days = calendar.monthrange(filter_year, filter_month)
    for day in range(1, num_days + 1):
        if day not in daily_revenue:
            daily_revenue[day] = 0

    # Format for chart
    max_revenue = max(daily_revenue.values()) if daily_revenue.values() else 1
    chart_data = [
        {
            'day': d,
            'revenue': v
        }
        for d, v in sorted(daily_revenue.items())
    ]

    vehicle_counts = db.session.query(
        Car.vehicle_type,
        func.count(ReceptionSlip.id).label('count')
    ).join(ReceptionSlip, ReceptionSlip.car_id == Car.id) \
        .filter(
        extract('month', ReceptionSlip.reception_date) == filter_month,
        extract('year', ReceptionSlip.reception_date) == filter_year
    ).group_by(Car.vehicle_type).all()

    vehicle_stats = []
    total_vehicles = 0

    for v_type, count in vehicle_counts:
        vehicle_type = v_type if v_type else 'Unknown'
        vehicle_stats.append({
            'type': vehicle_type,
            'count': count
        })
        total_vehicles += count

    from app.models import RepairSlip

    category_counts = db.session.query(
        RepairDetail.category,
        func.count(RepairDetail.id).label('count')
    ).join(RepairSlip, RepairDetail.repair_slip_id == RepairSlip.id) \
        .join(ReceptionSlip, RepairSlip.reception_slip_id == ReceptionSlip.id) \
        .filter(
        extract('month', ReceptionSlip.reception_date) == filter_month,
        extract('year', ReceptionSlip.reception_date) == filter_year
    ).group_by(RepairDetail.category).all()

    category_stats = []

    for cat, count in category_counts:
        cat_name = cat if cat else "Other"
        category_stats.append({
            'category': cat_name,
            'count': count
        })

    return render_template('admin/dashboard.html',
                           chart_data=chart_data,
                           total_revenue=total_revenue,
                           vehicle_stats=vehicle_stats,
                           category_stats=category_stats,
                           filter_day=filter_day,
                           filter_month=filter_month,
                           filter_year=filter_year)

@admin_bp.route('/components')
def components_page():
    components = component_dao.get_all_components()
    return render_template(
        'admin/accessories',
        components=components
    )


@admin_bp.route('/component/add', methods=['POST'])
def add_component():
    if not check_admin():
        return redirect(url_for('main.login'))

    name = request.form['name']
    current_price = float(request.form['current_price'])
    stock_quantity = int(request.form.get('stock_quantity', 0))

    new_component = Component(
        name=name,
        current_price=current_price,
        stock_quantity=stock_quantity
    )

    db.session.add(new_component)
    db.session.commit()

    flash('New component added successfully!')
    return redirect(url_for('admin.components_page'))


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


@admin_bp.route('/accessories')
def accessories():
    if not check_admin():
        return redirect(url_for('main.login'))

    components = component_dao.get_all_active()

    component_stats = []
    for comp in components:
        used_count = db.session.query(func.count(RepairDetail.id)) \
            .filter(RepairDetail.component_id == comp.id) \
            .scalar()

        imported = comp.stock_quantity + used_count

        component_stats.append({
            'id': comp.id,
            'code': f'P{str(comp.id).zfill(3)}',
            'name': comp.name,
            'imported': imported,
            'used': used_count,
            'inventory': comp.stock_quantity,
            'price': comp.current_price
        })

    most_used = sorted(component_stats, key=lambda x: x['used'], reverse=True)[:5]

    most_imported = sorted(component_stats, key=lambda x: x['imported'], reverse=True)[:5]

    total_inventory = sum(c['inventory'] for c in component_stats)

    edit_component = None
    edit_id = request.args.get('edit_id')
    if edit_id:
        edit_component = component_dao.get_component_by_id(int(edit_id))

    return render_template('admin/accessories.html',
                           components=component_stats,
                           most_used=most_used,
                           most_imported=most_imported,
                           total_inventory=total_inventory,
                           edit_component=edit_component)


@admin_bp.route('/accessories/update-price/<int:component_id>', methods=['POST'])
def update_accessory_price(component_id):
    if not check_admin():
        return redirect(url_for('main.login'))

    try:
        new_price = float(request.form['price'])
        component_dao.update_component(component_id, current_price=new_price)
        flash('Price updated successfully!')
    except ValueError:
        flash('Invalid price format!')

    return redirect(url_for('admin.accessories'))


@admin_bp.route('/accessories/batch-update', methods=['POST'])
def batch_update_prices():
    if not check_admin():
        return redirect(url_for('main.login'))

    updated_count = 0
    for key, value in request.form.items():
        if key.startswith('price_'):
            component_id = int(key.split('_')[1])
            try:
                new_price = float(value)
                if new_price > 0:
                    component_dao.update_component(component_id, current_price=new_price)
                    updated_count += 1
            except ValueError:
                continue

    flash(f'{updated_count} prices updated successfully!')
    return redirect(url_for('admin.accessories'))


@admin_bp.route('/vat-settings')
def vat_settings():
    if not check_admin():
        return redirect(url_for('main.login'))

    vat_rate = settings_dao.get_setting_float('vat_rate', 10.0)
    max_cars = settings_dao.get_setting_int('max_cars_per_day', 30)

    return render_template('admin/vat_settings.html',
                           vat_rate=vat_rate,
                           max_cars=max_cars)


@admin_bp.route('/vat-settings/update-vat', methods=['POST'])
def update_vat_rate():
    if not check_admin():
        return redirect(url_for('main.login'))

    try:
        new_vat = float(request.form['vat_rate'])
        if new_vat < 0 or new_vat > 100:
            flash('VAT rate must be between 0% and 100%')
        else:
            settings_dao.set_setting('vat_rate', new_vat)
            flash('VAT rate updated successfully!')
    except ValueError:
        flash('Invalid VAT rate format!')

    return redirect(url_for('admin.vat_settings'))


@admin_bp.route('/vat-settings/update-vehicle-limit', methods=['POST'])
def update_vehicle_limit():
    if not check_admin():
        return redirect(url_for('main.login'))

    try:
        new_limit = int(request.form['max_cars'])
        if new_limit < 1 or new_limit > 1000:
            flash('Vehicle limit must be between 1 and 1000')
        else:
            settings_dao.set_setting('max_cars_per_day', new_limit)
            flash('Vehicle limit updated successfully!')
    except ValueError:
        flash('Invalid vehicle limit format!')

    return redirect(url_for('admin.vat_settings'))




# TESTING

@admin_bp.route('/low-stock-alert')
def low_stock_alert():
    if not check_admin():
        return redirect(url_for('main.login'))

    threshold = ComponentDAO.get_low_stock_threshold()

    components = ComponentDAO.get_low_stock_components()

    components_data = []
    thirty_days_ago = datetime.now() - timedelta(days=30)

    for comp in components:
        # Thống kê sử dụng 30 ngày
        recent_usage = db.session.query(func.sum(RepairDetail.quantity)) \
            .join(RepairSlip, RepairDetail.repair_slip_id == RepairSlip.id) \
            .filter(
                RepairDetail.component_id == comp.id,
                RepairSlip.start_date >= thirty_days_ago
            ).scalar() or 0

        if comp.stock_quantity == 0:
            status = 'out'
            status_text = 'Out of Stock'
            status_color = '#DC3545'
        else:
            status = 'low'
            status_text = 'Low Stock'
            status_color = '#FFA500'

        components_data.append({
            'id': comp.id,
            'name': comp.name,
            'current_stock': comp.stock_quantity,
            'price': comp.current_price,
            'recent_usage': recent_usage,
            'status': status,
            'status_text': status_text,
            'status_color': status_color
        })

    return render_template(
        'admin/low_stock_alert.html',
        components=components_data,
        threshold=threshold,
        total_alerts=len(components_data)
    )


@admin_bp.route('/low-stock-count')
def low_stock_count():
    if not check_admin():
        return {'count': 0}

    return {
        'count': ComponentDAO.count_low_stock_components()
    }


@admin_bp.route('/update-stock-threshold', methods=['POST'])
def update_stock_threshold():
    if not check_admin():
        return redirect(url_for('main.login'))

    try:
        threshold = int(request.form['threshold'])
        if 0 <= threshold <= 100:
            SettingsDAO.set_setting('low_stock_threshold', threshold)
            flash('Warning threshold updated successfully.')
        else:
            flash('The value must be between 0 and 100.')
    except:
        flash('Invalid value')

    return redirect(url_for('admin.low_stock_alert'))


# Nhap hang vao

@admin_bp.route('/import-components', methods=['POST'])
def import_components():
    if not check_admin():
        return {'success': False, 'message': 'Unauthorized'}

    names = request.form.getlist('name[]')
    quantities = request.form.getlist('quantity[]')

    for name, qty, price in zip(names, quantities):
        component = Component.query.filter_by(name=name, is_deleted=False).first()

        if component:
            component.stock_quantity += int(qty)
        else:
            component = Component(
                name=name,
                stock_quantity=int(qty),
            )
            db.session.add(component)

    db.session.commit()
    return {'success': True}
