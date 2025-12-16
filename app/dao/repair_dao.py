from app.models import RepairSlip, RepairDetail, ReceptionSlip, Car, Component
from app import db
from datetime import datetime


def create_repair_slip(reception_slip_id, technician_id):
    """Create a new repair slip"""
    repair = RepairSlip(
        reception_slip_id=reception_slip_id,
        technician_id=technician_id,
        start_date=datetime.now()
    )
    db.session.add(repair)
    db.session.commit()
    return repair


def get_repair_by_id(repair_id):
    """Get repair slip by ID with related info"""
    return db.session.query(RepairSlip, ReceptionSlip, Car)\
        .join(ReceptionSlip, RepairSlip.reception_slip_id == ReceptionSlip.id)\
        .join(Car, ReceptionSlip.car_id == Car.id)\
        .filter(RepairSlip.id == repair_id)\
        .first()


def get_repair_only_by_id(repair_id):
    """Get repair slip only by ID"""
    return RepairSlip.query.get(repair_id)


def get_repair_by_reception_id(reception_slip_id):
    """Get repair slip by reception slip ID"""
    return RepairSlip.query.filter(RepairSlip.reception_slip_id == reception_slip_id).first()


def get_repairs_by_technician(technician_id, status=None):
    """Get repairs assigned to technician"""
    query = db.session.query(RepairSlip, ReceptionSlip, Car)\
        .join(ReceptionSlip, RepairSlip.reception_slip_id == ReceptionSlip.id)\
        .join(Car, ReceptionSlip.car_id == Car.id)\
        .filter(RepairSlip.technician_id == technician_id)
    
    if status:
        query = query.filter(ReceptionSlip.status == status)
    
    return query.order_by(RepairSlip.start_date.desc()).all()


def get_repair_details(repair_id):
    """Get all repair details for a repair slip"""
    return db.session.query(RepairDetail, Component)\
        .outerjoin(Component, RepairDetail.component_id == Component.id)\
        .filter(RepairDetail.repair_slip_id == repair_id)\
        .all()


def get_repair_details_only(repair_id):
    """Get repair details only"""
    return RepairDetail.query.filter(RepairDetail.repair_slip_id == repair_id).all()


def add_repair_detail(repair_slip_id, component_id, quantity, price_at_time, category=None, labor_fee=0):
    """Add a repair detail item"""
    detail = RepairDetail(
        repair_slip_id=repair_slip_id,
        component_id=component_id,
        quantity=quantity,
        price_at_time=price_at_time,
        category=category,
        labor_fee=labor_fee
    )
    db.session.add(detail)
    db.session.commit()
    return detail


def get_repair_detail_by_id(detail_id):
    """Get repair detail by ID"""
    return RepairDetail.query.get(detail_id)


def update_repair_detail(detail_id, component_id=None, quantity=None, price_at_time=None, category=None, labor_fee=None):
    """Update repair detail"""
    detail = RepairDetail.query.get(detail_id)
    if detail:
        if component_id is not None:
            detail.component_id = component_id
        if quantity is not None:
            detail.quantity = quantity
        if price_at_time is not None:
            detail.price_at_time = price_at_time
        if category is not None:
            detail.category = category
        if labor_fee is not None:
            detail.labor_fee = labor_fee
        db.session.commit()
    return detail


def delete_repair_detail(detail_id):
    """Delete repair detail"""
    detail = RepairDetail.query.get(detail_id)
    if detail:
        repair_slip_id = detail.repair_slip_id
        db.session.delete(detail)
        db.session.commit()
        return repair_slip_id
    return None


def finish_repair(repair_id):
    """Mark repair as finished"""
    repair = RepairSlip.query.get(repair_id)
    if repair:
        repair.end_date = datetime.now()
        db.session.commit()
    return repair
