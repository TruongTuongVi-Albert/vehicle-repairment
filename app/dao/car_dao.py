from app.models import Car
from app import db


def get_car_by_plate(license_plate):
    """Get car by license plate"""
    return Car.query.filter(Car.license_plate == license_plate).first()


def get_car_by_id(car_id):
    """Get car by ID"""
    return Car.query.get(car_id)


def create_car(license_plate, owner_name, phone_number=None, address=None, email=None, vehicle_type=None, color=None):
    """Create a new car"""
    car = Car(
        license_plate=license_plate,
        owner_name=owner_name,
        phone_number=phone_number,
        address=address,
        email=email,
        vehicle_type=vehicle_type,
        color=color
    )
    db.session.add(car)
    db.session.commit()
    return car


def update_car(car_id, owner_name=None, phone_number=None, address=None, email=None, vehicle_type=None, color=None):
    """Update car info"""
    car = Car.query.get(car_id)
    if car:
        if owner_name is not None:
            car.owner_name = owner_name
        if phone_number is not None:
            car.phone_number = phone_number
        if address is not None:
            car.address = address
        if email is not None:
            car.email = email
        if vehicle_type is not None:
            car.vehicle_type = vehicle_type
        if color is not None:
            car.color = color
        db.session.commit()
    return car


def create_or_update_car(license_plate, owner_name, phone_number=None, address=None, email=None, vehicle_type=None, color=None):
    """Create or update car by license plate"""
    car = get_car_by_plate(license_plate)
    if car:
        return update_car(car.id, owner_name, phone_number, address, email, vehicle_type, color)
    else:
        return create_car(license_plate, owner_name, phone_number, address, email, vehicle_type, color)
