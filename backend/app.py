# backend/app.py
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from datetime import datetime
import os, time

from models import (
    db, File, User,
    generate_reset_token, verify_reset_token
)
from config import Config

# ───────────────── Flask factory ──────────────────────────────
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# ──────────────── Login / session setup ───────────────────────
login_manager = LoginManager()
login_manager.init_app(app)         # no redirect
login_manager.login_view = None     # disable 302

@login_manager.user_loader
def load_user(uid):
    return db.session.get(User, int(uid))     # SQLAlchemy 2 style

@login_manager.unauthorized_handler
def api_unauthorized():
    return jsonify({"error": "unauthenticated"}), 401

# ──────────────── CORS (SPA on :8080) ─────────────────────────
CORS(app, supports_credentials=True)

# ──────────────── Health check ────────────────────────────────
@app.route('/')
def index():
    return {"message": "Flask backend is running."}

# ──────────────── File endpoints ──────────────────────────────
@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    f = request.files.get('file')
    if not f:
        return {"error": "No file provided"}, 400

    filename = secure_filename(f.filename)
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    f.save(path)

    rec = File(filename=filename, mimetype=f.mimetype,
               path=path, owner_id=current_user.id)
    db.session.add(rec)
    db.session.commit()
    return {"message": "Upload successful", "file_id": rec.id}, 201


@app.route('/files', methods=['GET'])
@login_required
def list_files():
    files = File.query.filter_by(owner_id=current_user.id).all()
    return jsonify([{"id": f.id, "name": f.filename} for f in files])


@app.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    f = File.query.get_or_404(file_id)
    if f.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403
    return send_from_directory(app.config['UPLOAD_FOLDER'], f.filename)

@app.route('/delete/<int:file_id>', methods=['DELETE'])
@login_required
def delete_file(file_id):
    f = File.query.get_or_404(file_id)
    if f.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403

    try:
        os.remove(f.path)
    except FileNotFoundError:
        pass

    db.session.delete(f)
    db.session.commit()
    return {"message": "File deleted successfully"}, 200

# ──────────────── Auth endpoints ──────────────────────────────
@app.route('/register', methods=['POST'])
def register():
    data = request.json or {}
    if User.query.filter_by(username=data.get('username')).first():
        return {"error": "Username already exists"}, 400
    if User.query.filter_by(email=data.get('email')).first():
        return {"error": "Email already registered"}, 400

    user = User(username=data['username'], email=data['email'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return {"message": "Registered successfully."}, 200


@app.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    user = User.query.filter_by(username=data.get('username')).first()
    if user and user.check_password(data.get('password', '')):
        login_user(user)
        return {"message": "Login successful"}
    return {"error": "Invalid credentials"}, 401


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return {"message": "Logged out"}

# ────────── Password-reset (forgot-pw) endpoints ──────────────
@app.route('/request-reset', methods=['POST'])
def request_reset():
    email = request.json.get('email', '')
    user  = User.query.filter_by(email=email).first()
    if user:
        tok = generate_reset_token(user)
        reset_url = f"{request.host_url}reset-password/{tok}"
        print("🔒 reset link:", reset_url)   # TODO: send email in prod
    return {"message": "If that e-mail exists, a reset link was sent"}, 200


@app.route('/reset-password/<token>', methods=['POST'])
def reset_password(token):
    user = verify_reset_token(token)
    if not user:
        return {"error": "Invalid or expired token"}, 400

    new_pwd = request.json.get('password', '')
    if len(new_pwd) < 6:
        return {"error": "Password too short"}, 400

    user.set_password(new_pwd)
    db.session.commit()
    return {"message": "Password updated"}, 200

# ────────── Change password while logged-in ───────────────────
@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.json or {}
    cur = data.get('current_password', '')
    new = data.get('new_password', '')

    if not current_user.check_password(cur):
        return {"error": "Current password is wrong"}, 400

    current_user.set_password(new)
    db.session.commit()
    return {"message": "Password updated"}, 200

# ────────── Bootstrapping & run ───────────────────────────────
if __name__ == '__main__':
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

    MAX_RETRIES = 10
    for attempt in range(MAX_RETRIES):
        try:
            with app.app_context():
                db.create_all()
                print("✅ tables:", inspect(db.engine).get_table_names())
                break
        except OperationalError:
            print(f"⏳ MySQL not ready ({attempt+1}/{MAX_RETRIES})…")
            time.sleep(3)
    else:
        print("❌ DB connection failed"); exit(1)

    app.run(host='0.0.0.0', port=5001)