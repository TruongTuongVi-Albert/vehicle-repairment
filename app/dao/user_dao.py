from app.models import User
from app import db


def get_user_by_id(user_id):
    """Get user by ID"""
    return User.query.get(user_id)


def auth_user(username, password):
    """Authenticate user with username and password"""
    return User.query.filter(
        User.username == username,
        User.password == password
    ).first()


def get_all_users():
    """Get all users"""
    return User.query.all()


def get_users_by_role(role):
    """Get users by role"""
    return User.query.filter(User.role == role).all()
