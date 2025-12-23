from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, Float, Enum, DateTime
from sqlalchemy.orm import relationship
from app import db, app
from flask_login import UserMixin
from enum import Enum as PyEnum
from datetime import datetime


class UserRole(PyEnum):
    ADMIN = 'admin'
    RECEPTION = 'reception'
    TECHNICIAN = 'technician'
    CASHIER = 'cashier'


class SlipStatus(PyEnum):
    PENDING = 'pending'
    WAITING = 'waiting'
    REPAIRING = 'repairing'
    COMPLETED = 'completed'
    PAID = 'paid'


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # Using String instead of Enum for compatibility
    full_name = Column(String(100))

    def __str__(self):
        return self.username


class Car(db.Model):
    __tablename__ = 'cars'
    
    id = Column(Integer, primary_key=True)
    license_plate = Column(String(20), unique=True, nullable=False)
    owner_name = Column(String(100), nullable=False)
    phone_number = Column(String(20))
    address = Column(String(255))
    email = Column(String(100))
    vehicle_type = Column(String(50))
    color = Column(String(50))
    
    reception_slips = relationship('ReceptionSlip', backref='car', lazy=True)

    def __str__(self):
        return self.license_plate


class ReceptionSlip(db.Model):
    __tablename__ = 'reception_slips'
    
    id = Column(Integer, primary_key=True)
    car_id = Column(Integer, ForeignKey('cars.id'), nullable=False)
    reception_date = Column(DateTime, default=datetime.now)
    status = Column(String(20), default='pending')  # pending, waiting, repairing, completed, paid
    description = Column(Text)
    
    repair_slip = relationship('RepairSlip', backref='reception_slip', uselist=False, lazy=True)

    def __str__(self):
        return f"Slip #{self.id}"


class Component(db.Model):
    __tablename__ = 'components'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    current_price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False)

    def __str__(self):
        return self.name


class RepairSlip(db.Model):
    __tablename__ = 'repair_slips'
    
    id = Column(Integer, primary_key=True)
    reception_slip_id = Column(Integer, ForeignKey('reception_slips.id'), nullable=False)
    technician_id = Column(Integer, ForeignKey('users.id'))
    start_date = Column(DateTime, default=datetime.now)
    end_date = Column(DateTime)
    
    technician = relationship('User', backref='repairs', lazy=True)
    details = relationship('RepairDetail', backref='repair_slip', lazy=True)

    def __str__(self):
        return f"Repair #{self.id}"


class RepairDetail(db.Model):
    __tablename__ = 'repair_details'
    
    id = Column(Integer, primary_key=True)
    repair_slip_id = Column(Integer, ForeignKey('repair_slips.id'), nullable=False)
    component_id = Column(Integer, ForeignKey('components.id'), nullable=True)
    quantity = Column(Integer, default=1)
    price_at_time = Column(Float, nullable=False)
    category = Column(String(250))
    labor_fee = Column(Float, default=0)
    
    component = relationship('Component', lazy=True)

    def __str__(self):
        return f"Detail #{self.id}"


class Invoice(db.Model):
    __tablename__ = 'invoices'
    
    id = Column(Integer, primary_key=True)
    repair_slip_id = Column(Integer, ForeignKey('repair_slips.id'), nullable=False)
    cashier_id = Column(Integer, ForeignKey('users.id'))
    total_amount = Column(Float, nullable=False)
    vat_rate = Column(Float, default=10.0)
    created_at = Column(DateTime, default=datetime.now)
    payment_method = Column(String(50), default='cash')
    
    repair_slip = relationship('RepairSlip', backref='invoice', lazy=True)
    cashier = relationship('User', lazy=True)

    def __str__(self):
        return f"Invoice #{self.id}"


class SystemSetting(db.Model):
    __tablename__ = 'system_settings'
    
    setting_key = Column(String(50), primary_key=True)
    setting_value = Column(String(255))

    def __str__(self):
        return f"{self.setting_key}: {self.setting_value}"


# Initialize database with seed data
# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all()
#
#         # Add default users if not exist
#         if not User.query.filter_by(username='admin').first():
#             users = [
#                 User(username='admin', password='123', role='admin', full_name='Administrator'),
#                 User(username='reception', password='123', role='reception', full_name='Receptionist A'),
#                 User(username='tech', password='123', role='technician', full_name='Technician B'),
#                 User(username='cashier', password='123', role='cashier', full_name='Cashier C'),
#             ]
#             db.session.add_all(users)
#             db.session.commit()
#             print("Default users created.")
#
#         # Add default settings if not exist
#         if not SystemSetting.query.filter_by(setting_key='max_cars_per_day').first():
#             settings = [
#                 SystemSetting(setting_key='max_cars_per_day', setting_value='30'),
#                 SystemSetting(setting_key='vat_rate', setting_value='10'),
#             ]
#             db.session.add_all(settings)
#             db.session.commit()
#             print("Default settings created.")
#
#         print("Database initialized.")
