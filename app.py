from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from config import Config
import random

app = Flask(__name__)
app.config.from_object(Config)

# Database connection helper
def get_db_connection():
    conn = mysql.connector.connect(
        host=app.config['MYSQL_HOST'],
        port=app.config.get('MYSQL_PORT', 3306),
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB'],
        ssl_disabled=app.config.get('MYSQL_SSL_DISABLED', False)
    )
    return conn

@app.route('/')
def index():
    if 'user_id' in session:
        return render_template('home.html')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Filter params
    from datetime import datetime
    now = datetime.now()
    filter_day = request.args.get('day')
    filter_month = request.args.get('month', now.month)
    filter_year = request.args.get('year', now.year)
    
    try:
        filter_month = int(filter_month)
        filter_year = int(filter_year)
        if filter_day: filter_day = int(filter_day)
    except ValueError:
        filter_month = now.month
        filter_year = now.year
        filter_day = None

    # 1. Revenue Data
    total_revenue = 0
    import calendar
    _, num_days = calendar.monthrange(filter_year, filter_month)
    
    # Init days with 0
    daily_revenue = {day: 0 for day in range(1, num_days + 1)}
    
    cursor.execute("""
        SELECT DAY(created_at) as day, SUM(total_amount) as total
        FROM invoices
        WHERE MONTH(created_at) = %s AND YEAR(created_at) = %s
        GROUP BY DAY(created_at)
    """, (filter_month, filter_year))
    
    results = cursor.fetchall()
    for row in results:
        daily_revenue[row['day']] = float(row['total'])
        total_revenue += float(row['total'])
        
    # Format for chart
    max_revenue = max(daily_revenue.values()) if daily_revenue.values() else 0
    chart_data = [{'label': d, 'value': v, 'percent': (v/max_revenue*100 if max_revenue else 0)} 
                  for d, v in daily_revenue.items()]

    # 2. Vehicle Types Ratio
    cursor.execute("""
        SELECT c.vehicle_type, COUNT(*) as count
        FROM reception_slips rs
        JOIN cars c ON rs.car_id = c.id
        WHERE MONTH(rs.reception_date) = %s AND YEAR(rs.reception_date) = %s
        GROUP BY c.vehicle_type
    """, (filter_month, filter_year))
    
    vehicle_counts = cursor.fetchall()
    
    stats = {}
    pie_stops = {}
    total_vehicles = 0
    print(vehicle_counts)
    
    for row in vehicle_counts:
        v_type = row['vehicle_type']
        count = row['count']
        stats[v_type] = stats.get(v_type, 0) + count
        total_vehicles += count

    prev_v_type = None
    for v_type in stats:
        # v_type is string, cannot use - 1
        if pie_stops.get(prev_v_type):
            pie_stops[v_type] = {
                'from': pie_stops[prev_v_type]['to'],
                'to': pie_stops[prev_v_type]['to'] + stats[v_type] / total_vehicles * 360
            }
        else:
            pie_stops[v_type] = {
                'from': 0,
                'to': stats[v_type] / total_vehicles * 360
            }
        prev_v_type = v_type

    # Generate random colors for each vehicle type
    colors = {}
    for v_type in stats:
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        colors[v_type] = 'rgb(' + str(r) + ',' + str(g) + ',' + str(b) + ')'

    # 2.5 Category Stats (for Horizontal Bar Chart)
    cursor.execute("""
        SELECT rd.category, COUNT(*) as count
        FROM repair_details rd
        JOIN repair_slips r ON rd.repair_slip_id = r.id
        JOIN reception_slips rs ON r.reception_slip_id = rs.id
        WHERE MONTH(rs.reception_date) = %s AND YEAR(rs.reception_date) = %s
        GROUP BY rd.category
    """, (filter_month, filter_year))
    
    category_counts = cursor.fetchall()
    category_stats = {}
    total_items = 0
    
    for row in category_counts:
        cat = row['category']
        # Handle empty category
        if not cat: cat = "Uncategorized"
        
        count = row['count']
        category_stats[cat] = category_stats.get(cat, 0) + count
        total_items += count
        
    # Generate colors for categories
    category_colors = {}
    for cat in category_stats:
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        category_colors[cat] = 'rgb(' + str(r) + ',' + str(g) + ',' + str(b) + ')'

    # 3. Settings & Components
    cursor.execute("SELECT * FROM system_settings")
    settings_list = cursor.fetchall()
    settings = {item['setting_key']: item['setting_value'] for item in settings_list}
    
    cursor.execute("SELECT * FROM components WHERE is_deleted = FALSE")
    components = cursor.fetchall()
    
    # 4. Handle Edit Component
    edit_component = None
    edit_id = request.args.get('edit_id')
    if edit_id:
        cursor.execute("SELECT * FROM components WHERE id = %s", (edit_id,))
        edit_component = cursor.fetchone()

    cursor.close()
    conn.close()

    print(pie_stops)

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

@app.route('/admin/settings', methods=['POST'])
def admin_update_settings():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    
    max_cars = request.form['max_cars']
    vat_rate = request.form['vat_rate']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO system_settings (setting_key, setting_value) VALUES ('max_cars_per_day', %s) ON DUPLICATE KEY UPDATE setting_value = %s", (max_cars, max_cars))
    cursor.execute("INSERT INTO system_settings (setting_key, setting_value) VALUES ('vat_rate', %s) ON DUPLICATE KEY UPDATE setting_value = %s", (vat_rate, vat_rate))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Settings updated.')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/component/add', methods=['POST'])
def admin_add_component():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    
    name = request.form['name']
    price = request.form['price']
    stock = request.form.get('stock', 0)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO components (name, current_price, stock_quantity) VALUES (%s, %s, %s)", (name, price, stock))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Component added.')
    flash('Component added.')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/component/update/<int:component_id>', methods=['POST'])
def admin_update_component(component_id):
    if session.get('role') != 'admin': return redirect(url_for('login'))
    
    name = request.form['name']
    price = request.form['price']
    stock = request.form.get('stock', 0)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE components SET name=%s, current_price=%s, stock_quantity=%s WHERE id=%s", 
                   (name, price, stock, component_id))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Component updated.')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/component/delete/<int:component_id>', methods=['POST'])
def admin_delete_component(component_id):
    if session.get('role') != 'admin': return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE components SET is_deleted = TRUE WHERE id=%s", (component_id,))
        conn.commit()
        flash('Component deleted.')
    except mysql.connector.Error as err:
        flash(f'Error: Cannot delete component. It might be in use.')
        
    cursor.close()
    conn.close()
    
    return redirect(url_for('admin_dashboard'))

def get_reception_data(cursor):
    # Get max cars setting
    cursor.execute("SELECT setting_value FROM system_settings WHERE setting_key = 'max_cars_per_day'")
    row = cursor.fetchone()
    max_cars = int(row['setting_value']) if row else 30
    
    # Get count of cars received today
    cursor.execute("SELECT COUNT(*) as count FROM reception_slips WHERE DATE(reception_date) = CURDATE()")
    cars_today_count = cursor.fetchone()['count']
    
    # Get list of cars/slips
    cursor.execute("""
        SELECT rs.*, c.license_plate, c.owner_name, c.phone_number , c.vehicle_type
        FROM reception_slips rs 
        JOIN cars c ON rs.car_id = c.id 
        ORDER BY rs.reception_date DESC
    """)
    slips = cursor.fetchall()
    
    return max_cars, cars_today_count, slips

@app.route('/reception')
def reception_home():
    if session.get('role') != 'reception' and session.get('role') != 'admin': return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    max_cars, cars_today_count, slips = get_reception_data(cursor)
    
    cursor.close()
    conn.close()

    print(slips)
    
    return render_template('reception/home.html', slips=slips, cars_today_count=cars_today_count, max_cars=max_cars)

@app.route('/reception/add', methods=['GET', 'POST'])
def reception_add_car():
    if session.get('role') != 'reception' and session.get('role') != 'admin': return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        # Check max cars limit
        cursor.execute("SELECT setting_value FROM system_settings WHERE setting_key = 'max_cars_per_day'")
        row = cursor.fetchone()
        max_cars = int(row['setting_value']) if row else 30
        
        cursor.execute("SELECT COUNT(*) as count FROM reception_slips WHERE DATE(reception_date) = CURDATE()")
        current_count = cursor.fetchone()['count']
        
        if current_count >= max_cars:
            flash(f'Daily limit of {max_cars} cars reached. Cannot receive more cars today.')
            cursor.close()
            conn.close()
            return redirect(url_for('reception_home'))
            
        # Process form
        license_plate = request.form['license_plate']
        owner_name = request.form['owner_name']
        phone = request.form['phone_number']
        address = request.form['address']
        email = request.form.get('email', '') # Optional
        description = request.form.get('description', '')
        
        # New fields
        vehicle_type = request.form.get('vehicle_type', 'Car')
        color = request.form.get('color', '')
        status = request.form.get('status', 'pending')
        
        # Check if car exists or create new
        cursor.execute("SELECT id FROM cars WHERE license_plate = %s", (license_plate,))
        car = cursor.fetchone()
        
        if car:
            car_id = car['id']
            # Update car info
            cursor.execute("UPDATE cars SET owner_name=%s, phone_number=%s, address=%s, email=%s, vehicle_type=%s, color=%s WHERE id=%s",
                           (owner_name, phone, address, email, vehicle_type, color, car_id))
        else:
            cursor.execute("INSERT INTO cars (license_plate, owner_name, phone_number, address, email, vehicle_type, color) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                           (license_plate, owner_name, phone, address, email, vehicle_type, color))
            car_id = cursor.lastrowid
            
        # Check if updating existing slip
        slip_id = request.args.get('slip_id')
        if slip_id:
            cursor.execute("UPDATE reception_slips SET car_id=%s, description=%s, status=%s WHERE id=%s",
                           (car_id, description, status, slip_id))
            flash('Reception slip updated successfully!')
        else:
            # Create reception slip
            print(status)
            cursor.execute("INSERT INTO reception_slips (car_id, description, status) VALUES (%s, %s, %s)",
                           (car_id, description, status))
            flash('Car received successfully!')
            
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('reception_home'))
    
    # GET request - show modal
    max_cars, cars_today_count, slips = get_reception_data(cursor)
    
    # Check if editing
    slip_id = request.args.get('slip_id')
    slip = None
    if slip_id:
        cursor.execute("""
            SELECT rs.*, c.license_plate, c.owner_name, c.phone_number, c.address, c.email, c.vehicle_type, c.color
            FROM reception_slips rs 
            JOIN cars c ON rs.car_id = c.id 
            WHERE rs.id = %s
        """, (slip_id,))
        slip = cursor.fetchone()
    
    cursor.close()
    conn.close()
    from datetime import datetime
    now_date = datetime.now().strftime('%Y-%m-%d')
    # Render home with modal='add'
    return render_template('reception/home.html', slips=slips, cars_today_count=cars_today_count, max_cars=max_cars, modal='add', slip=slip, now_date=now_date)

@app.route('/reception/detail/<int:slip_id>')
def reception_detail(slip_id):
    if session.get('role') != 'reception' and session.get('role') != 'admin': return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get common data for background
    max_cars, cars_today_count, slips = get_reception_data(cursor)
    
    # Get specific slip details
    cursor.execute("""
        SELECT rs.*, c.license_plate, c.owner_name, c.phone_number, c.address, c.email, c.vehicle_type, c.color
        FROM reception_slips rs 
        JOIN cars c ON rs.car_id = c.id 
        WHERE rs.id = %s
    """, (slip_id,))
    slip = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if not slip:
        flash('Reception slip not found.')
        return redirect(url_for('reception_home'))
        
    return render_template('reception/home.html', slips=slips, cars_today_count=cars_today_count, max_cars=max_cars, modal='detail', slip=slip)

def get_technician_data(cursor, filter_status=None):
    # Base query for all relevant slips (pending, waiting, repairing, completed)
    # We need to handle two cases: 
    # 1. Slips in reception_slips (pending/waiting) - no repair_slip yet
    # 2. Slips in repair_slips (repairing/completed) - has repair_slip
    
    slips = []
    
    # 1. Get Pending/Waiting slips (from reception_slips)
    if not filter_status or filter_status in ['quote', 'waiting']:
        cursor.execute("""
            SELECT rs.*, c.license_plate, c.owner_name, c.vehicle_type, c.color, 
                   NULL as repair_id, rs.reception_date as date_display
            FROM reception_slips rs 
            JOIN cars c ON rs.car_id = c.id 
            WHERE rs.status IN ('pending', 'waiting')
            ORDER BY rs.reception_date ASC
        """)
        slips.extend(cursor.fetchall())

    # 2. Get Repairing/Completed slips (from repair_slips)
    if not filter_status or filter_status in ['repairing', 'complete']:
        # Map 'complete' filter to 'completed' db status if needed, or just use 'completed'
        db_status = 'completed' if filter_status == 'complete' else filter_status
        
        query = """
            SELECT r.id as repair_id, rs.id as id, rs.status, 
                   c.license_plate, c.owner_name, c.vehicle_type, c.color, 
                   r.start_date as date_display, rs.reception_date
            FROM repair_slips r
            JOIN reception_slips rs ON r.reception_slip_id = rs.id
            JOIN cars c ON rs.car_id = c.id
            WHERE r.technician_id = %s
        """
        params = [session['user_id']]
        
        if db_status:
            query += " AND rs.status = %s"
            params.append(db_status)
            
        query += " ORDER BY r.start_date DESC"
        
        cursor.execute(query, tuple(params))
        slips.extend(cursor.fetchall())
    
    # Sort combined list by date_display if needed, but for now just returning combined
    # If no filter, we might want to sort everything by date
    if not filter_status:
        slips.sort(key=lambda x: x['date_display'] if x['date_display'] else x['reception_date'], reverse=True)
        
    return slips

@app.route('/technician')
def technician_home():
    if session.get('role') != 'technician' and session.get('role') != 'admin': return redirect(url_for('login'))
    
    filter_status = request.args.get('filter')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    slips = get_technician_data(cursor, filter_status)
    
    cursor.close()
    conn.close()
    
    return render_template('technician/home.html', slips=slips, current_filter=filter_status)

@app.route('/technician/start/<int:slip_id>', methods=['POST'])
def technician_start_repair(slip_id):
    if session.get('role') != 'technician' and session.get('role') != 'admin': return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create repair slip
    cursor.execute("INSERT INTO repair_slips (reception_slip_id, technician_id) VALUES (%s, %s)",
                   (slip_id, session['user_id']))
    repair_id = cursor.lastrowid
    
    # Update reception slip status
    cursor.execute("UPDATE reception_slips SET status = 'repairing' WHERE id = %s", (slip_id,))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Repair started. Please add items.')
    return redirect(url_for('technician_add_item_view', repair_id=repair_id))

@app.route('/technician/detail/<int:slip_id>')
def technician_view_detail(slip_id):
    if session.get('role') != 'technician' and session.get('role') != 'admin': return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get common data for background
    filter_status = request.args.get('filter')
    slips = get_technician_data(cursor, filter_status)
    
    # Check if this slip is already in repair (has repair_slip entry)
    cursor.execute("""
        SELECT r.id as repair_id, rs.id as reception_id, rs.status, rs.description,
               c.license_plate, c.owner_name, c.phone_number, c.address, c.vehicle_type, c.color
        FROM reception_slips rs
        JOIN cars c ON rs.car_id = c.id
        LEFT JOIN repair_slips r ON rs.id = r.reception_slip_id
        WHERE rs.id = %s
    """, (slip_id,))
    repair = cursor.fetchone()
    
    if not repair:
        cursor.close()
        conn.close()
        flash('Slip not found.')
        return redirect(url_for('technician_home'))
        
    items = []
    if repair['repair_id']:
        # Fetch items if repair exists
        cursor.execute("""
            SELECT rd.*, c.name, c.current_price as price 
            FROM repair_details rd
            LEFT JOIN components c ON rd.component_id = c.id
            WHERE rd.repair_slip_id = %s
        """, (repair['repair_id'],))
        items = cursor.fetchall()
    
    # Get components for dropdown (if needed for add item)
    cursor.execute("SELECT * FROM components WHERE is_deleted = FALSE")
    components = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('technician/home.html', slips=slips, current_filter=filter_status, modal='detail', repair=repair, items=items, components=components)

@app.route('/technician/repair/<int:repair_id>/add', methods=['GET'])
def technician_add_item_view(repair_id):
    if session.get('role') != 'technician' and session.get('role') != 'admin': return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get common data
    slips = get_technician_data(cursor)
    
    # Get repair info
    cursor.execute("""
        SELECT r.id as repair_id, rs.id as reception_id, rs.status, rs.description,
               c.license_plate, c.owner_name, c.phone_number, c.address, c.vehicle_type, c.color
        FROM repair_slips r
        JOIN reception_slips rs ON r.reception_slip_id = rs.id
        JOIN cars c ON rs.car_id = c.id
        WHERE r.id = %s
    """, (repair_id,))
    repair = cursor.fetchone()
    
    # Get items
    cursor.execute("""
        SELECT rd.*, c.name, c.current_price as price 
        FROM repair_details rd
        LEFT JOIN components c ON rd.component_id = c.id
        WHERE rd.repair_slip_id = %s
    """, (repair_id,))
    items = cursor.fetchall()
    
    cursor.execute("SELECT * FROM components WHERE is_deleted = FALSE")
    components = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('technician/home.html', slips=slips, modal='add_item', repair=repair, items=items, components=components)

@app.route('/technician/repair/<int:repair_id>/edit/<int:item_id>', methods=['GET'])
def technician_edit_item_view(repair_id, item_id):
    if session.get('role') != 'technician' and session.get('role') != 'admin': return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get common data
    slips = get_technician_data(cursor)
    
    # Get repair info
    cursor.execute("""
        SELECT r.id as repair_id, rs.id as reception_id, rs.status, rs.description,
               c.license_plate, c.owner_name, c.phone_number, c.address, c.vehicle_type, c.color
        FROM repair_slips r
        JOIN reception_slips rs ON r.reception_slip_id = rs.id
        JOIN cars c ON rs.car_id = c.id
        WHERE r.id = %s
    """, (repair_id,))
    repair = cursor.fetchone()
    
    # Get items
    cursor.execute("""
        SELECT rd.*, c.name, c.current_price as price 
        FROM repair_details rd
        LEFT JOIN components c ON rd.component_id = c.id
        WHERE rd.repair_slip_id = %s
    """, (repair_id,))
    items = cursor.fetchall()
    
    # Get specific item to edit
    cursor.execute("""
        SELECT rd.*, c.name, c.current_price as price 
        FROM repair_details rd
        LEFT JOIN components c ON rd.component_id = c.id
        WHERE rd.id = %s
    """, (item_id,))
    edit_item = cursor.fetchone()
    
    cursor.execute("SELECT * FROM components WHERE is_deleted = FALSE")
    components = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('technician/home.html', slips=slips, modal='add_item', repair=repair, items=items, components=components, edit_item=edit_item)

@app.route('/technician/repair/<int:repair_id>/add_item', methods=['POST'])
def technician_add_item(repair_id):
    if session.get('role') != 'technician' and session.get('role') != 'admin': return redirect(url_for('login'))
    
    component_id = request.form.get('component_id')
    quantity = int(request.form.get('quantity', 1))
    category = request.form.get('category', '')
    current_price = request.form.get('current_price', 0)
    
    # Clean expense input
    try:
        current_price = float(current_price)
    except ValueError:
        current_price = 0
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    expense = 0
    if component_id:
        # Get component price
        cursor.execute("SELECT current_price FROM components WHERE id = %s", (component_id,))
        component = cursor.fetchone()
        if component:
            expense = component['current_price']
    else:
        component_id = None

    print(repair_id, component_id, quantity, current_price, category, expense)
    cursor.execute("INSERT INTO repair_details (repair_slip_id, component_id, quantity, price_at_time, category, labor_fee) VALUES (%s, %s, %s, %s, %s, %s)",
                   (repair_id, component_id, quantity, current_price, category, expense))
    conn.commit()
    flash('Item added.')
    
    cursor.close()
    conn.close()
    return redirect(url_for('technician_view_detail', slip_id=repair_id))

@app.route('/technician/item/update/<int:item_id>', methods=['POST'])
def technician_update_item(item_id):
    if session.get('role') != 'technician' and session.get('role') != 'admin': return redirect(url_for('login'))
    
    component_id = request.form.get('component_id')
    quantity = int(request.form.get('quantity', 1))
    category = request.form.get('category', '')
    current_price = request.form.get('current_price', 0)
    
    # Clean expense input
    try:
        current_price = float(current_price)
    except ValueError:
        current_price = 0
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    expense = 0
    if component_id:
        # Get component price
        cursor.execute("SELECT current_price FROM components WHERE id = %s", (component_id,))
        component = cursor.fetchone()
        if component:
            expense = component['current_price']
    else:
        component_id = None
        
    # Get repair_id for redirect
    cursor.execute("SELECT repair_slip_id FROM repair_details WHERE id = %s", (item_id,))
    row = cursor.fetchone()
    repair_id = row['repair_slip_id'] if row else None

    if repair_id:
        cursor.execute("UPDATE repair_details SET component_id=%s, quantity=%s, price_at_time=%s, category=%s, labor_fee=%s WHERE id=%s",
                       (component_id, quantity, current_price, category, expense, item_id))
        conn.commit()
        flash('Item updated.')
    
    cursor.close()
    conn.close()
    
    if repair_id:
        return redirect(url_for('technician_view_detail', slip_id=repair_id))
    return redirect(url_for('technician_home'))

@app.route('/technician/item/delete/<int:item_id>', methods=['POST'])
def technician_delete_item(item_id):
    if session.get('role') != 'technician' and session.get('role') != 'admin': return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get repair_id for redirect
    cursor.execute("SELECT repair_slip_id FROM repair_details WHERE id = %s", (item_id,))
    row = cursor.fetchone()
    repair_id = row[0] if row else None
    
    if repair_id:
        cursor.execute("DELETE FROM repair_details WHERE id = %s", (item_id,))
        conn.commit()
        flash('Item deleted.')
        
    cursor.close()
    conn.close()
    
    if repair_id:
        return redirect(url_for('technician_view_detail', slip_id=repair_id))
    return redirect(url_for('technician_home'))

@app.route('/technician/repair/<int:repair_id>/finish', methods=['POST'])
def technician_finish_repair(repair_id):
    if session.get('role') != 'technician' and session.get('role') != 'admin': return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get reception slip id
    cursor.execute("SELECT reception_slip_id FROM repair_slips WHERE id = %s", (repair_id,))
    reception_slip_id = cursor.fetchone()[0]
    
    # Update status
    cursor.execute("UPDATE reception_slips SET status = 'completed' WHERE id = %s", (reception_slip_id,))
    cursor.execute("UPDATE repair_slips SET end_date = NOW() WHERE id = %s", (repair_id,))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Repair finished. Sent to Cashier.')
    return redirect(url_for('technician_home'))
    
@app.route('/cashier')
def cashier_home():
    if session.get('role') != 'cashier' and session.get('role') != 'admin': return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get VAT rate
    cursor.execute("SELECT setting_value FROM system_settings WHERE setting_key = 'vat_rate'")
    row = cursor.fetchone()
    vat_rate = float(row['setting_value']) if row else 10.0

    # Get filter
    filter_status = request.args.get('filter')
    
    # Build query based on filter
    query = """
        SELECT rs.*, c.license_plate, c.owner_name, c.phone_number, r.id as repair_id, r.end_date
        FROM reception_slips rs 
        JOIN cars c ON rs.car_id = c.id 
        JOIN repair_slips r ON rs.id = r.reception_slip_id
    """
    
    params = []
    if filter_status == 'completed':
        query += " WHERE rs.status = 'completed'"
    elif filter_status == 'paid':
        query += " WHERE rs.status = 'paid'"
    else:
        # Show both if no filter
        query += " WHERE rs.status IN ('completed', 'paid')"
        
    query += " ORDER BY r.end_date DESC"
    
    cursor.execute(query, params)
    completed_slips = cursor.fetchall()
    
    # Calculate totals for each slip
    for slip in completed_slips:
        cursor.execute("""
            SELECT SUM(price_at_time * quantity + labor_fee) as subtotal
            FROM repair_details
            WHERE repair_slip_id = %s
        """, (slip['repair_id'],))
        result = cursor.fetchone()
        slip['total_amount'] = float(result['subtotal']) if result['subtotal'] else 0.0

    # Get recent invoices
    cursor.execute("""
        SELECT i.*, c.license_plate
        FROM invoices i
        JOIN repair_slips r ON i.repair_slip_id = r.id
        JOIN reception_slips rs ON r.reception_slip_id = rs.id
        JOIN cars c ON rs.car_id = c.id
        ORDER BY i.created_at DESC LIMIT 10
    """)
    recent_invoices = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('cashier/home.html', completed_slips=completed_slips, recent_invoices=recent_invoices, vat_rate=vat_rate, current_filter=filter_status)

@app.route('/cashier/invoice/<int:repair_id>')
def cashier_invoice(repair_id):
    if session.get('role') != 'cashier' and session.get('role') != 'admin': return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get repair info
    cursor.execute("""
        SELECT r.id as repair_id, c.license_plate, c.owner_name, c.phone_number, c.address, c.vehicle_type, c.color, rs.reception_date as reception_date, rs.status as status
        FROM repair_slips r
        JOIN reception_slips rs ON r.reception_slip_id = rs.id
        JOIN cars c ON rs.car_id = c.id
        WHERE r.id = %s
    """, (repair_id,))
    repair = cursor.fetchone()
    
    # Get items
    cursor.execute("""
        SELECT rd.*, c.name 
        FROM repair_details rd
        LEFT JOIN components c ON rd.component_id = c.id
        WHERE rd.repair_slip_id = %s
    """, (repair_id,))
    items = cursor.fetchall()
    
    # Get VAT rate
    cursor.execute("SELECT setting_value FROM system_settings WHERE setting_key = 'vat_rate'")
    vat_rate = float(cursor.fetchone()['setting_value'])
    
    # Calculate totals
    subtotal = sum(item['price_at_time'] * item['quantity'] + item['labor_fee'] for item in items)
    vat_amount = float(subtotal) * (vat_rate / 100)
    total_amount = float(subtotal) + vat_amount
    
    cursor.close()
    conn.close()
    
    from datetime import datetime
    today = datetime.now().strftime('%d/%m/%Y')
    
    return render_template('cashier/invoice.html', repair=repair, items=items, 
                           subtotal=subtotal, vat_rate=vat_rate, vat_amount=vat_amount, 
                           total_amount=total_amount, today=today)

@app.route('/cashier/pay/<int:repair_id>', methods=['POST'])
def cashier_process_payment(repair_id):
    if session.get('role') != 'cashier' and session.get('role') != 'admin': return redirect(url_for('login'))
    
    total_amount = float(request.form['total_amount'])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get VAT rate again to be safe
    cursor.execute("SELECT setting_value FROM system_settings WHERE setting_key = 'vat_rate'")
    vat_rate = float(cursor.fetchone()[0])
    
    # Create invoice
    cursor.execute("""
        INSERT INTO invoices (repair_slip_id, cashier_id, total_amount, vat_rate)
        VALUES (%s, %s, %s, %s)
    """, (repair_id, session['user_id'], total_amount, vat_rate))
    
    # Update reception slip status to 'paid'
    cursor.execute("SELECT reception_slip_id FROM repair_slips WHERE id = %s", (repair_id,))
    reception_slip_id = cursor.fetchone()[0]
    
    cursor.execute("UPDATE reception_slips SET status = 'paid' WHERE id = %s", (reception_slip_id,))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Payment processed successfully!')
    return redirect(url_for('cashier_home'))

if __name__ == '__main__':
    app.run(debug=True)
