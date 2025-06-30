"""
Authentication routes for Document Center
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
import os

from ..models import db, User, Folder
from ..config import Config

bp = Blueprint('auth', __name__)


@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password') or not data.get('email'):
        return jsonify({"message": "Username, email, and password are required"}), 400

    if User.query.filter_by(username=data['username']).first() or \
       User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "User already exists"}), 400

    user = User(username=data['username'], email=data['email'], grade=data.get('grade', 33))
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()

    # create root folder + disk dir
    root = Folder(name='Root folder', owner_id=user.id, parent_id=None)
    db.session.add(root)
    db.session.commit()
    os.makedirs(os.path.join(Config.UPLOAD_FOLDER, user.username),
                exist_ok=True)

    return {"message": "Registered successfully."}


@bp.route('/session-status', methods=['GET'])
def session_status():
    """Get current session status and user info"""
    if current_user.is_authenticated:
        return jsonify({
            "authenticated": True,
            "user": {
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email,
                "is_admin": current_user.is_admin
            }
        })
    else:
        return jsonify({"authenticated": False, "user": None})


@bp.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return {"error": "Username and password required"}, 400
    
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        # Force logout any existing session first
        if current_user.is_authenticated:
            logout_user()
        
        login_user(user, remember=False, fresh=True)
        return jsonify({
            "message": "Login successful",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin
            }
        })
    return {"error": "Invalid credentials"}, 401


@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return {"message": "Logged out"}


@bp.route('/request-reset', methods=['POST'])
def request_reset():
    from ..models import generate_reset_token
    email = request.json.get('email', '')
    user = User.query.filter_by(email=email).first()
    if user:
        tok = generate_reset_token(user)
        print("🔒 reset link:", f"{request.host_url}reset-password/{tok}")
    return {"message": "If that e-mail exists, a reset link was sent"}


@bp.route('/reset-password/<token>', methods=['POST'])
def reset_password(token):
    from ..models import verify_reset_token
    user = verify_reset_token(token)
    if not user:
        return {"error": "Invalid or expired token"}, 400
    new_pwd = request.json.get('password', '')
    if len(new_pwd) < 6:
        return {"error": "Password too short"}, 400
    user.set_password(new_pwd)
    db.session.commit()
    return {"message": "Password updated"}


@bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.json or {}
    cur, new = data.get('current_password', ''), data.get('new_password', '')
    if not current_user.check_password(cur):
        return {"error": "Current password is wrong"}, 400
    current_user.set_password(new)
    db.session.commit()
    return {"message": "Password updated"}


@bp.route('/user-info', methods=['GET'])
@login_required
def get_user_info():
    """Get current user's profile information"""
    return jsonify({
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "grade": current_user.grade,
        "is_admin": current_user.is_admin,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    })


@bp.route('/users', methods=['GET'])
@login_required
def get_users():
    """Get list of all users for reviewer assignment"""
    users = User.query.filter(User.id != current_user.id).all()
    return jsonify([{
        "id": user.id,
        "username": user.username,
        "email": user.email
    } for user in users]) 