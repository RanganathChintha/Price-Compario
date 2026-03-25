from flask import Flask
from flask_cors import CORS
import os
from config import Config, DevelopmentConfig, ProductionConfig
from app.utils.logger import setup_logger
from app.utils.errors import register_error_handlers


def create_app(config_name=None):
    """Application factory pattern"""
    # Setup logging
    logger = setup_logger()
    
    app = Flask(__name__)
    
    # Load configuration
    if config_name == 'development':
        app.config.from_object(DevelopmentConfig)
    elif config_name == 'production':
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(Config)
    
    # Enable CORS
    CORS(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Initialize services (will be imported when needed)
    app.config['CACHE_TTL'] = app.config.get('CACHE_TIMEOUT', 300)
    
    # Register blueprints
    from app.routes.main import main_bp
    app.register_blueprint(main_bp)
    
    logger.info(f"Application started in {app.config.get('DEBUG', 'production')} mode")
    
    return app