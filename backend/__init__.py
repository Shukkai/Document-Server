"""
Document Center Flask Application Factory
"""

from flask import Flask, jsonify
from flask_cors import CORS
from flask_login import LoginManager
from prometheus_flask_exporter import PrometheusMetrics
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import os

from .models import db, User
from .config import Config
from .init_db import create_admin_and_test_users
from .redis_config import init_redis

def create_app(config_class=Config):
    """Application factory pattern for Flask app creation."""
    
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Set secret key explicitly (matching original tmp.py)
    app.secret_key = os.getenv("SECRET_KEY", "dev-secret")
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize Redis
    init_redis(app)
    
    # Initialize monitoring
    metrics = PrometheusMetrics(app)
    
    # Initialize login manager
    login_manager = LoginManager()
    login_manager.login_view = None  # Return JSON, no 302 redirect
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(uid):
        return db.session.get(User, int(uid))
    
    @login_manager.unauthorized_handler
    def _unauth():
        from flask import jsonify
        return jsonify({"error": "unauthenticated"}), 401
    
    # Initialize CORS
    CORS(app, supports_credentials=True)
    
    # Initialize OAuth
    load_dotenv()
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

    # Set frontend configuration (matching original tmp.py globals)
    FRONTEND_PORT = os.getenv("FRONTEND_PORT", 80)
    FRONTEND_ROOT = f"http://localhost:{FRONTEND_PORT}" if FRONTEND_PORT else "http://localhost:8080"
    app.config['FRONTEND_PORT'] = FRONTEND_PORT
    app.config['FRONTEND_ROOT'] = FRONTEND_ROOT

    # Only initialize OAuth if proper credentials are provided
    if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET and GOOGLE_CLIENT_ID != "your-google-client-id" and GOOGLE_CLIENT_SECRET != "your-google-client-secret":
        oauth = OAuth(app)
        google = oauth.register(
            name='google',
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            access_token_params=None,
            authorize_params=None,
            api_base_url='https://www.googleapis.com/oauth2/v1/',
            client_kwargs={
                'scope': 'openid email profile',
            },
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration'
        )
        
        # Store OAuth instance in app config for routes to access
        app.config['OAUTH_INSTANCE'] = oauth
        app.logger.info("OAuth Google client initialized successfully")
    else:
        app.config['OAUTH_INSTANCE'] = None
        app.logger.warning("OAuth Google client not initialized - missing or invalid credentials. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.")
    
    # Create test users
    with app.app_context():
        try:
            create_admin_and_test_users(app, db)
        except Exception as e:
            app.logger.warning(f"Could not create test users: {e}")
    
    # Register blueprints
    try:
        from .routes import auth, files, folders, reviews, admin, oauth_routes, redis_routes
        app.register_blueprint(auth.bp)
        app.register_blueprint(files.bp)
        app.register_blueprint(folders.bp)
        app.register_blueprint(reviews.bp)
        app.register_blueprint(admin.bp)
        app.register_blueprint(oauth_routes.bp)
        app.register_blueprint(redis_routes.bp)
    except Exception as e:
        app.logger.error(f"Error registering blueprints: {e}")
        raise
    
    # Register error handlers
    try:
        from .utils.error_handlers import register_error_handlers
        register_error_handlers(app)
    except Exception as e:
        app.logger.warning(f"Could not register error handlers: {e}")
    
    # Health check route (moved from files blueprint to match prototype)
    @app.route('/')
    def health():
        return {"message": "Flask backend is running."}
    
    return app
