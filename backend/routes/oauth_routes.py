"""
OAuth routes for Document Center
"""

from flask import Blueprint, redirect, url_for, session, current_app
from flask_login import login_user
from authlib.integrations.flask_client import OAuth
import os

from ..models import db, User, Folder
from ..config import Config

bp = Blueprint('oauth', __name__, url_prefix='/auth')


@bp.route('/google/login')
def google_login():
    """Redirect to Google OAuth login"""
    try:
        oauth = current_app.config.get('OAUTH_INSTANCE')
        if not oauth:
            current_app.logger.error("OAuth instance not found in app config")
            return {"error": "OAuth is not configured. Please contact the administrator to set up Google OAuth credentials."}, 503
            
        google = oauth.create_client('google')
        
        if not google:
            current_app.logger.error("Google OAuth client not found - check environment variables")
            current_app.logger.error(f"GOOGLE_CLIENT_ID: {os.getenv('GOOGLE_CLIENT_ID', 'NOT_SET')}")
            current_app.logger.error(f"GOOGLE_CLIENT_SECRET: {'SET' if os.getenv('GOOGLE_CLIENT_SECRET') else 'NOT_SET'}")
            return {"error": "OAuth is not properly configured. Please contact the administrator."}, 503
        
        # Match original tmp.py logic exactly
        redirect_uri = url_for('oauth.google_callback', _external=True)

        FRONTEND_ROOT = current_app.config.get('FRONTEND_ROOT', 'http://localhost')
        FRONTEND_PORT = current_app.config.get('FRONTEND_PORT', 80)
        
        current_app.logger.info(f"Redirect URI: {redirect_uri}")
        current_app.logger.info(f"Frontend Port: {FRONTEND_PORT}")

        if FRONTEND_PORT == 80 or FRONTEND_PORT == "80":
            if "localhost" in redirect_uri:
                FRONTEND_ROOT = f"http://localhost"
            elif "127.0.0.1" in redirect_uri:
                FRONTEND_ROOT = f"http://127.0.0.1"

            redirect_uri = "http://localhost/api/auth/google/callback"
            current_app.logger.info(f"Redirect URI: {redirect_uri}")
            return google.authorize_redirect(redirect_uri)

        elif "localhost" in redirect_uri and "localhost:5001" not in redirect_uri:
            localhost_name = redirect_uri.split("://")[1].split("/")[0]
            redirect_uri = redirect_uri.replace(localhost_name, "localhost:5001")
            FRONTEND_ROOT = f"http://localhost:{FRONTEND_PORT}"

        elif "127.0.0.1" in redirect_uri and "127.0.0.1:5001" not in redirect_uri:
            localhost_name = redirect_uri.split("://")[1].split("/")[0]
            redirect_uri = redirect_uri.replace(localhost_name, "127.0.0.1:5001")
            FRONTEND_ROOT = f"http://127.0.0.1:{FRONTEND_PORT}"

        return google.authorize_redirect(redirect_uri)
    except Exception as e:
        current_app.logger.error(f"Error in google_login: {str(e)}")
        return {"error": f"OAuth error: {str(e)}"}, 500


@bp.route('/google/callback')
def google_callback():
    """Handle Google OAuth callback"""
    try:
        oauth = current_app.config.get('OAUTH_INSTANCE')
        if not oauth:
            current_app.logger.error("OAuth instance not found in app config")
            return {"error": "OAuth is not configured. Please contact the administrator to set up Google OAuth credentials."}, 503
            
        google = oauth.create_client('google')  # Create a Google OAuth client
        
        if not google:
            current_app.logger.error("Google OAuth client not found in callback")
            return {"error": "OAuth is not properly configured. Please contact the administrator."}, 503
        
        token = google.authorize_access_token()
        user_info = google.get('userinfo').json()

        email = user_info.get('email')
        if not email:
            return {"error": "No email found in Google user info"}, 400

        user = User.query.filter_by(email=email).first()
        if user is None:
            base = email.split('@')[0]
            username = base
            i = 1
            while User.query.filter_by(username=username).first():
                username = f"{base}{i}"; i += 1

            user = User(username=username, email=email, grade=33)
            user.set_password(os.urandom(16).hex())   # SSO 帳號不用真正密碼

            db.session.add(user)
            db.session.commit()

            root = Folder(name='Root folder', owner_id=user.id, parent_id=None)
            db.session.add(root)
            db.session.commit()

            os.makedirs(os.path.join(Config.UPLOAD_FOLDER, username),
                    exist_ok=True)

        # login the user
        login_user(user, remember=False, fresh=True)

        FRONTEND_ROOT = current_app.config.get('FRONTEND_ROOT', 'http://localhost')
        FRONTEND_PORT = current_app.config.get('FRONTEND_PORT', 80)
        FRONTEND_ROOT = f"http://localhost:{FRONTEND_PORT}" if FRONTEND_PORT else "http://localhost:8080"
        return redirect(f"{FRONTEND_ROOT}/oauth2/success")
    except Exception as e:
        current_app.logger.error(f"Error in google_callback: {str(e)}")
        return {"error": f"OAuth callback error: {str(e)}"}, 500 