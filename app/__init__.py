from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
from dotenv import load_dotenv
from urllib.parse import quote

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or 'dev_key_very_secret'

# Database configuration
# MYSQL_HOST = os.getenv('MYSQL_HOST') or 'localhost'
# MYSQL_PORT = os.getenv('MYSQL_PORT') or 3306
# MYSQL_USER = os.getenv('MYSQL_USER') or 'root'
# MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD') or 'root'
# MYSQL_DB = os.getenv('MYSQL_DB') or 'car_repair_db'

# app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4" % quote('admin@123')
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:%s@localhost/car_repair_db?charset=utf8mb4" % quote('admin@123')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] = 10

db = SQLAlchemy(app=app)
login_manager = LoginManager(app=app)
login_manager.login_view = 'main.login'

# Import models after db is created
from app import models

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))

# Register blueprints
from app.index import main_bp
from app.admin import admin_bp
from app.reception import reception_bp
from app.technician import technician_bp
from app.cashier import cashier_bp

app.register_blueprint(main_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(reception_bp, url_prefix='/reception')
app.register_blueprint(technician_bp, url_prefix='/technician')
app.register_blueprint(cashier_bp, url_prefix='/cashier')
