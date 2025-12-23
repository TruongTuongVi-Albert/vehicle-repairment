from app import app, db
from app.models import User, SystemSetting

with app.app_context():
    db.create_all()

    if not User.query.filter_by(username='admin').first():
        users = [
            User(username='admin', password='123', role='admin', full_name='Administrator'),
            User(username='reception', password='123', role='reception', full_name='Receptionist'),
            User(username='tech', password='123', role='technician', full_name='Technician'),
            User(username='cashier', password='123', role='cashier', full_name='Cashier'),
        ]
        db.session.add_all(users)
        db.session.commit()

    if not SystemSetting.query.filter_by(setting_key='vat_rate').first():
        settings = [
            SystemSetting(setting_key='vat_rate', setting_value='10'),
            SystemSetting(setting_key='max_cars_per_day', setting_value='30')
        ]
        db.session.add_all(settings)
        db.session.commit()

    print(" Database initialized")
