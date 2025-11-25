import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ae7e055a98993414c240404c74d9ecf9'
    
    # Database configuration (supports both MySQL and SQLite)
    DATABASE_URL = os.environ.get('DATABASE_URL')
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or 'Shashi@30'
    MYSQL_DB = os.environ.get('MYSQL_DB') or 'beauty_salon'

    # Email configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'shr23cs@cmrit.ac.in'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'gjrpypiyltuwdybk'
    MAIL_DEFAULT_SENDER = ('Beauty Salon', os.environ.get('MAIL_USERNAME') or 'shr23cs@cmrit.ac.in')

class ProductionConfig(Config):
    DEBUG = False
    
class DevelopmentConfig(Config):
    DEBUG = True
