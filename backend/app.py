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
    db, File, User, Folder,
    generate_reset_token, verify_reset_token
)
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = None

@login_manager.user_loader
def load_user(uid):
    return db.session.get(User, int(uid))

@login_manager.unauthorized_handler
def api_unauthorized():
    return jsonify({"error": "unauthenticated"}), 401

CORS(app, supports_credentials=True)

@app.route('/')
def index():
    return {"message": "Flask backend is running."}

def build_folder_path(folder):
    names = []
    while folder:
        names.insert(0, folder.name)
        folder = folder.parent
    return os.path.join(app.config['UPLOAD_FOLDER'], current_user.username, *names)

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    f = request.files.get('file')
    folder_id = request.form.get('folder_id', type=int)

    if not f:
        return {"error": "No file provided"}, 400

    filename = secure_filename(f.filename)
    folder = Folder.query.get(folder_id) if folder_id else Folder.query.filter_by(owner_id=current_user.id, parent_id=None).first()
    folder_path = build_folder_path(folder) if folder else os.path.join(app.config['UPLOAD_FOLDER'], current_user.username)
    os.makedirs(folder_path, exist_ok=True)

    full_path = os.path.join(folder_path, filename)
    f.save(full_path)

    rec = File(filename=filename, mimetype=f.mimetype,
               path=full_path, owner_id=current_user.id, folder_id=folder.id if folder else None)
    db.session.add(rec)
    db.session.commit()
    return {"message": "Upload successful", "file_id": rec.id}, 201

@app.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    f = File.query.get_or_404(file_id)
    if f.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403
    return send_from_directory(os.path.dirname(f.path), os.path.basename(f.path))

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

@app.route('/folders', methods=['GET'])
@login_required
def get_nested_folders():
    def serialize_folder(folder):
        return {
            "id": folder.id,
            "name": folder.name,
            "parent_id": folder.parent_id,
            "files": [
                {
                    "id": f.id,
                    "name": f.filename,
                    "mimetype": f.mimetype,
                    "uploaded_at": f.uploaded_at.isoformat()
                } for f in folder.files
            ],
            "children": [serialize_folder(child) for child in folder.subfolders]
        }
    root = Folder.query.filter_by(owner_id=current_user.id, parent_id=None).first()
    if not root:
        return jsonify({"id": None, "name": "", "files": [], "children": []})
    return jsonify(serialize_folder(root))

@app.route('/folders', methods=['POST'])
@login_required
def create_folder():
    data = request.json or {}
    name = data.get('name', '').strip()
    parent_id = data.get('parent_id')

    if not name:
        return {"error": "Folder name required"}, 400

    parent_folder = Folder.query.get(parent_id) if parent_id else Folder.query.filter_by(owner_id=current_user.id, parent_id=None).first()
    existing = Folder.query.filter_by(owner_id=current_user.id, name=name, parent_id=parent_folder.id if parent_folder else None).first()
    if existing:
        return {"error": "Folder already exists"}, 400

    base_path = build_folder_path(parent_folder) if parent_folder else os.path.join(app.config['UPLOAD_FOLDER'], current_user.username)
    os.makedirs(base_path, exist_ok=True)
    new_path = os.path.join(base_path, name)
    os.makedirs(new_path, exist_ok=True)

    folder = Folder(name=name, owner_id=current_user.id, parent_id=parent_folder.id if parent_folder else None)
    db.session.add(folder)
    db.session.commit()
    return {"message": "Folder created", "folder_id": folder.id}, 201

@app.route('/folders/<int:folder_id>', methods=['DELETE'])
@login_required
def delete_folder(folder_id):
    folder = Folder.query.get_or_404(folder_id)
    if folder.owner_id != current_user.id:
        return {"error": "Access denied"}, 403
    if folder.parent_id is None:
        return {"error": "Cannot delete root folder"}, 400
    db.session.delete(folder)
    db.session.commit()
    return {"message": "Folder deleted"}, 200

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

    root = Folder(name=data['username'], owner_id=user.id, parent_id=None)
    db.session.add(root)
    db.session.commit()

    user_folder_path = os.path.join(app.config['UPLOAD_FOLDER'], data['username'])
    os.makedirs(user_folder_path, exist_ok=True)

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

@app.route('/request-reset', methods=['POST'])
def request_reset():
    email = request.json.get('email', '')
    user = User.query.filter_by(email=email).first()
    if user:
        tok = generate_reset_token(user)
        reset_url = f"{request.host_url}reset-password/{tok}"
        print("🔒 reset link:", reset_url)
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