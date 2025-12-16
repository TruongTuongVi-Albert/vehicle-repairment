from app.models import Component
from app import db


def get_all_active():
    """Get all active (not deleted) components"""
    return Component.query.filter(Component.is_deleted == False).all()


def get_all_components():
    """Get all components including deleted"""
    return Component.query.all()


def get_component_by_id(component_id):
    """Get component by ID"""
    return Component.query.get(component_id)


def add_component(name, current_price, stock_quantity=0):
    """Add a new component"""
    component = Component(
        name=name,
        current_price=current_price,
        stock_quantity=stock_quantity,
        is_deleted=False
    )
    db.session.add(component)
    db.session.commit()
    return component


def update_component(component_id, name=None, current_price=None, stock_quantity=None):
    """Update component"""
    component = Component.query.get(component_id)
    if component:
        if name is not None:
            component.name = name
        if current_price is not None:
            component.current_price = current_price
        if stock_quantity is not None:
            component.stock_quantity = stock_quantity
        db.session.commit()
    return component


def soft_delete_component(component_id):
    """Soft delete component (set is_deleted=True)"""
    component = Component.query.get(component_id)
    if component:
        component.is_deleted = True
        db.session.commit()
        return True
    return False
