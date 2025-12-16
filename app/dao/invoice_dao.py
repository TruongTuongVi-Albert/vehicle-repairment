from app.models import Invoice, RepairSlip, ReceptionSlip, Car
from app import db
from sqlalchemy import func, extract
from datetime import datetime


def create_invoice(repair_slip_id, cashier_id, total_amount, vat_rate):
    """Create a new invoice"""
    invoice = Invoice(
        repair_slip_id=repair_slip_id,
        cashier_id=cashier_id,
        total_amount=total_amount,
        vat_rate=vat_rate,
        created_at=datetime.now()
    )
    db.session.add(invoice)
    db.session.commit()
    return invoice


def get_invoice_by_repair_id(repair_id):
    """Get invoice by repair slip ID"""
    return Invoice.query.filter(Invoice.repair_slip_id == repair_id).first()


def get_recent_invoices(limit=10):
    """Get recent invoices with car info"""
    return db.session.query(Invoice, Car)\
        .join(RepairSlip, Invoice.repair_slip_id == RepairSlip.id)\
        .join(ReceptionSlip, RepairSlip.reception_slip_id == ReceptionSlip.id)\
        .join(Car, ReceptionSlip.car_id == Car.id)\
        .order_by(Invoice.created_at.desc())\
        .limit(limit)\
        .all()


def get_revenue_by_month(month, year):
    """Get daily revenue for a month"""
    results = db.session.query(
        extract('day', Invoice.created_at).label('day'),
        func.sum(Invoice.total_amount).label('total')
    ).filter(
        extract('month', Invoice.created_at) == month,
        extract('year', Invoice.created_at) == year
    ).group_by(
        extract('day', Invoice.created_at)
    ).all()
    
    return {int(r.day): float(r.total) for r in results}


def get_total_revenue_by_month(month, year):
    """Get total revenue for a month"""
    result = db.session.query(
        func.sum(Invoice.total_amount).label('total')
    ).filter(
        extract('month', Invoice.created_at) == month,
        extract('year', Invoice.created_at) == year
    ).first()
    
    return float(result.total) if result.total else 0.0
