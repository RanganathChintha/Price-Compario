import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    GROK_API_KEY = os.environ.get('GROK_API_KEY')
    CACHE_TIMEOUT = int(os.environ.get('CACHE_TIMEOUT', 300))
    DEBUG = os.environ.get('FLASK_ENV') == 'development'


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False