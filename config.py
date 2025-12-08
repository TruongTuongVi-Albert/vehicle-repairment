import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_key_very_secret'
    MYSQL_HOST = os.getenv('MYSQL_HOST') or 'localhost'
    MYSQL_PORT = os.getenv('MYSQL_PORT') or 3306
    MYSQL_USER = os.getenv('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD') or 'root'
    MYSQL_DB = os.getenv('MYSQL_DB') or 'car_repair'
    MYSQL_SSL_DISABLED = False # Enforce SSL
