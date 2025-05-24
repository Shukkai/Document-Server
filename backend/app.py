# backend/app.py
from __future__ import annotations
import os, time
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user,
)
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError

from models import (
    db, File, Folder, User,
    generate_reset_token, verify_reset_token,
)
from config import Config

# ───────────────────────────── Flask & Login ─────────────────────────────
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager               = LoginManager()
login_manager.login_view    = None          #   ↳ return JSON, no 302
login_manager.init_app(app)

@login_manager.user_loader
def load_user(uid):          # SQLAlchemy 2.x: Session.get
    return db.session.get(User, int(uid))

@login_manager.unauthorized_handler
def _unauth():
    return jsonify({"error": "unauthenticated"}), 401

CORS(app, supports_credentials=True)

# ───────────────────── helper: build **absolute** disk path ──────────────
def folder_disk_path(folder: Folder | None, username: str) -> str:
    """
    Build uploads/<username>/… path for *folder*.
    If *folder* is None ⇒ returns user root folder.
    """
    parts: list[str] = []
    while folder and folder.parent_id is not None:   # stop at root
        parts.append(folder.name)
        folder = folder.parent
    parts.reverse()
    return os.path.join(app.config['UPLOAD_FOLDER'], username, *parts)

# ───────────────────────────────── Routes ─────────────────────────────────
@app.route('/')
def health():
    return {"message": "Flask backend is running."}

# ────────────── Upload ───────────────────────────────────────────────────
@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    f         = request.files.get('file')
    folder_id = request.form.get('folder_id', type=int)
    if not f:
        return {"error": "No file provided"}, 400

    # target folder (None → root)
    folder = Folder.query.get(folder_id) if folder_id else \
             Folder.query.filter_by(owner_id=current_user.id,
                                    parent_id=None).first()

    disk_dir = folder_disk_path(folder, current_user.username)
    os.makedirs(disk_dir, exist_ok=True)

    final_path = os.path.join(disk_dir, secure_filename(f.filename))
    f.save(final_path)

    rec = File(filename=f.filename, mimetype=f.mimetype,
               path=final_path, owner_id=current_user.id,
               folder_id=folder.id if folder else None)
    db.session.add(rec); db.session.commit()
    return {"message": "Upload successful", "file_id": rec.id}, 201

# ────────────── Download / Delete file ───────────────────────────────────
@app.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    rec = File.query.get_or_404(file_id)
    if rec.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403
    return send_from_directory(os.path.dirname(rec.path),
                               os.path.basename(rec.path))

@app.route('/delete/<int:file_id>', methods=['DELETE'])
@login_required
def delete_file(file_id):
    rec = File.query.get_or_404(file_id)
    if rec.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403
    try:
        os.remove(rec.path)
    except FileNotFoundError:
        pass
    db.session.delete(rec); db.session.commit()
    return {"message": "File deleted"}, 200

# ────────────── Folder tree (GET) ────────────────────────────────────────
@app.route('/folders', methods=['GET'])
@login_required
def get_folders():
    def ser(folder: Folder):
        return {
            "id": folder.id, "name": folder.name,
            "parent_id": folder.parent_id,
            "files": [
                {
                    "id": f.id, "name": f.filename,
                    "mimetype": f.mimetype,
                    "uploaded_at": f.uploaded_at.isoformat()
                } for f in folder.files
            ],
            "children": [ser(ch) for ch in folder.subfolders]
        }
    root = Folder.query.filter_by(owner_id=current_user.id,
                                  parent_id=None).first()
    return jsonify(ser(root) if root else
                   {"id": None, "name": "", "files": [], "children": []})

# ────────────── Create / Delete folder ───────────────────────────────────
@app.route('/folders', methods=['POST'])
@login_required
def create_folder():
    data      = request.json or {}
    name      = data.get('name', '').strip()
    parent_id = data.get('parent_id')
    if not name:
        return {"error": "Folder name required"}, 400

    parent = Folder.query.get(parent_id) if parent_id else \
             Folder.query.filter_by(owner_id=current_user.id,
                                    parent_id=None).first()

    # no duplicates among siblings
    if Folder.query.filter_by(owner_id=current_user.id,
                              parent_id=parent.id if parent else None,
                              name=name).first():
        return {"error": "Folder already exists"}, 400

    disk_dir = folder_disk_path(parent, current_user.username)
    os.makedirs(os.path.join(disk_dir, name), exist_ok=True)

    new = Folder(name=name, owner_id=current_user.id,
                 parent_id=parent.id if parent else None)
    db.session.add(new); db.session.commit()
    return {"message": "Folder created", "folder_id": new.id}, 201

@app.route('/folders/<int:fid>', methods=['DELETE'])
@login_required
def delete_folder(fid):
    fld = Folder.query.get_or_404(fid)
    if fld.owner_id != current_user.id:
        return {"error": "Access denied"}, 403
    if fld.parent_id is None:
        return {"error": "Cannot delete root folder"}, 400
    db.session.delete(fld); db.session.commit()
    return {"message": "Folder deleted"}

# ────────────── Move file ────────────────────────────────────────────────
# backend/app.py  ── keep all existing imports & helpers
# … above unchanged …

@app.route('/move-file', methods=['POST'])
@login_required
def move_file():
    """
    JSON body:
      { "file_id": 123, "target_folder_id": 7 }
    """
    data         = request.json or {}
    file_id      = data.get('file_id')
    target_id    = data.get('target_folder_id')

    rec          = File  .query.get_or_404(file_id)
    target       = Folder.query.get_or_404(target_id)

    # ── ownership guards ──────────────────────────────────────
    if rec.owner_id   != current_user.id:      return {"error": "Access denied"}, 403
    if target.owner_id!= current_user.id:      return {"error": "Access denied"}, 403

    # ── new disk location ------------------------------------
    dest_dir = folder_disk_path(target, current_user.username)
    os.makedirs(dest_dir, exist_ok=True)

    new_path = os.path.join(dest_dir, rec.filename)
    os.rename(rec.path, new_path)

    # ── update DB --------------------------------------------
    rec.folder_id = target.id
    rec.path      = new_path
    db.session.commit()

    return {"message": "File moved"} , 200

# ────────────── Auth & password flows (unchanged) ───────────────────────
@app.route('/register', methods=['POST'])
def register():
    data = request.json or {}
    if User.query.filter_by(username=data.get('username')).first():
        return {"error": "Username already exists"}, 400
    if User.query.filter_by(email=data.get('email')).first():
        return {"error": "Email already registered"}, 400

    user = User(username=data['username'], email=data['email'])
    user.set_password(data['password'])
    db.session.add(user); db.session.commit()

    # create root folder + disk dir
    root = Folder(name=user.username, owner_id=user.id, parent_id=None)
    db.session.add(root); db.session.commit()
    os.makedirs(os.path.join(Config.UPLOAD_FOLDER, user.username),
                exist_ok=True)

    return {"message": "Registered successfully."}

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
    user  = User.query.filter_by(email=email).first()
    if user:
        tok = generate_reset_token(user)
        print("🔒 reset link:", f"{request.host_url}reset-password/{tok}")
    return {"message": "If that e-mail exists, a reset link was sent"}

@app.route('/reset-password/<token>', methods=['POST'])
def reset_password(token):
    user = verify_reset_token(token)
    if not user:
        return {"error": "Invalid or expired token"}, 400
    new_pwd = request.json.get('password', '')
    if len(new_pwd) < 6:
        return {"error": "Password too short"}, 400
    user.set_password(new_pwd); db.session.commit()
    return {"message": "Password updated"}

@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.json or {}
    cur, new = data.get('current_password',''), data.get('new_password','')
    if not current_user.check_password(cur):
        return {"error":"Current password is wrong"}, 400
    current_user.set_password(new); db.session.commit()
    return {"message":"Password updated"}

# ────────────── Error: file too large ────────────────────────────────────
@app.errorhandler(RequestEntityTooLarge)
def too_large(_): return {"error":"File exceeds limit"}, 413

# ────────────── Bootstrapping ────────────────────────────────────────────
if __name__ == '__main__':
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    app.secret_key = os.getenv("SECRET_KEY", "dev-secret")

    for i in range(10):
        try:
            with app.app_context():
                db.create_all()
                print("✅ tables:", inspect(db.engine).get_table_names())
                break
        except OperationalError:
            print("⏳ waiting for MySQL…"); time.sleep(3)
    else:
        print("❌ DB not reachable"); exit(1)

    app.run(host='0.0.0.0', port=5001)