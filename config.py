import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    MAPBOX_API_KEY = os.getenv('MAPBOX_API_KEY', 'sk.eyJ1Ijoic2FyYWhzdWVlIiwiYSI6ImNtZ3o3MnZ0czBibXIybHI0eXN1enZyMW0ifQ.aC2sIPH5u-yyW_20g7T3dA')  # <-- Add this line

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}