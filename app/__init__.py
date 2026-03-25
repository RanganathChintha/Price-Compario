from flask import Flask
from flask_cors import CORS
import os
from config import Config, DevelopmentConfig, ProductionConfig
from app.utils.logger import setup_logger
from app.utils.errors import register_error_handlers
from app.middleware.performance import PerformanceMiddleware
from app.routes.analytics import analytics_bp
from app.routes.health import health_bp
from app.routes.sitemap import sitemap_bp


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
    
    # Setup performance middleware
    PerformanceMiddleware(app)
    
    # Register blueprints
    from app.routes.main import main_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(sitemap_bp)
    
    logger.info(f"Application started in {app.config.get('DEBUG', 'production')} mode")
    
    return app