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
    db, File, Folder, User, FileVersion,
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
    if not folder or folder.parent_id is None:
        return os.path.join(app.config['UPLOAD_FOLDER'], username)
    
    # Build the full path hierarchy recursively
    path_parts = []
    current = folder
    
    while current and current.parent_id is not None:
        path_parts.append(current.name)
        current = Folder.query.get(current.parent_id)
    
    path_parts.reverse()  # Reverse to get correct order
    return os.path.join(app.config['UPLOAD_FOLDER'], username, *path_parts)

def get_version_dir(username: str) -> str:
    """Get the .version directory path for a user"""
    version_dir = os.path.join(app.config['UPLOAD_FOLDER'], username, '.version')
    os.makedirs(version_dir, exist_ok=True)
    return version_dir

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

    # Create file record
    rec = File(filename=f.filename, mimetype=f.mimetype,
               path=final_path, owner_id=current_user.id,
               folder_id=folder.id if folder else None,
               current_version=1)  # Set initial version
    db.session.add(rec)
    db.session.flush()  # Get the file ID without committing

    # Create initial version record and store in .version directory
    version_dir = get_version_dir(current_user.username)
    version_path = os.path.join(version_dir, f"{rec.id}_v1_{secure_filename(f.filename)}")
    import shutil
    shutil.copy2(final_path, version_path)

    version = FileVersion(
        file_id=rec.id,
        version_number=1,
        path=version_path,
        comment="Initial version"
    )
    db.session.add(version)
    db.session.commit()
    
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
        # Delete the file record - this will cascade delete all related versions
        # due to the cascade relationship we just added
        db.session.delete(rec)
        db.session.commit()
        
        return {
            "message": "File deleted successfully.",
            "file_id": file_id
        }, 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting file {file_id}: {str(e)}")
        return {"error": "Failed to delete file"}, 500

@app.route('/list-deleted-files', methods=['GET'])
@login_required
def list_deleted_files():
    """
    List all files that have been deleted but still have version history.
    This helps users find files they might want to restore.
    """
    # Find all version records that don't have an associated file
    versions = db.session.query(FileVersion).outerjoin(File).filter(File.id == None).all()
    
    # Group versions by file_id to get the latest version for each deleted file
    deleted_files = {}
    for version in versions:
        if version.file_id not in deleted_files or version.version_number > deleted_files[version.file_id]['version_number']:
            deleted_files[version.file_id] = {
                'file_id': version.file_id,
                'version_number': version.version_number,
                'filename': os.path.basename(version.path).split('_', 1)[1],  # Remove version prefix
                'last_modified': version.uploaded_at.isoformat(),
                'size': os.path.getsize(version.path) if os.path.exists(version.path) else 0,
                'comment': version.comment
            }
    
    return jsonify(list(deleted_files.values()))

@app.route('/permanently-delete/<int:file_id>', methods=['DELETE'])
@login_required
def permanently_delete_file(file_id):
    """
    Permanently delete a file and all its versions.
    This is a destructive operation and cannot be undone.
    """
    # First check if the file exists
    file = File.query.get(file_id)
    if file:
        if file.owner_id != current_user.id and not current_user.is_admin:
            return {"error": "Access denied"}, 403
        db.session.delete(file)
    
    # Delete all versions
    versions = FileVersion.query.filter_by(file_id=file_id).all()
    for version in versions:
        try:
            if os.path.exists(version.path):
                os.remove(version.path)
        except FileNotFoundError:
            pass
        db.session.delete(version)
    
    db.session.commit()
    return {
        "message": "File and all its versions permanently deleted",
        "file_id": file_id
    }, 200

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
    
    def get_flat_folders(folder, depth=0):
        """Get a flat list of folders (excluding root) for dropdown"""
        folders = []
        if folder:
            for child in folder.subfolders:
                indent = '  ' * depth
                folders.append({
                    'id': child.id,
                    'name': f"{indent}{child.name}"
                })
                folders.extend(get_flat_folders(child, depth + 1))
        return folders
    
    root = Folder.query.filter_by(owner_id=current_user.id,
                                  parent_id=None).first()
    
    folder_tree = ser(root) if root else {"id": None, "name": "", "files": [], "children": []}
    flat_folders = get_flat_folders(root)
    
    return jsonify({
        "tree": folder_tree,
        "flat": flat_folders
    })

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

    # Create folder in the correct parent directory
    parent_disk_path = folder_disk_path(parent, current_user.username)
    disk_dir = os.path.join(parent_disk_path, name)
    os.makedirs(disk_dir, exist_ok=True)

    new = Folder(name=name, owner_id=current_user.id,
                 parent_id=parent.id if parent else None)
    db.session.add(new)
    db.session.commit()
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
@app.route('/move-file', methods=['POST'])
@login_required
def move_file():
    """
    JSON body:
      { "file_id": 123, "target_folder_id": 7 }
    Note: target_folder_id can be null for moving to root folder
    """
    data         = request.json or {}
    file_id      = data.get('file_id')
    target_id    = data.get('target_folder_id')

    rec = File.query.get_or_404(file_id)
    
    # Handle moving to root folder (target_id is None/null)
    if target_id is None:
        # Get user's root folder
        target = Folder.query.filter_by(owner_id=current_user.id, parent_id=None).first()
        if not target:
            return {"error": "Root folder not found"}, 404
    else:
        target = Folder.query.get_or_404(target_id)
        if target.owner_id != current_user.id:
            return {"error": "Access denied to target folder"}, 403

    # ── ownership guards ──────────────────────────────────────
    if rec.owner_id != current_user.id:
        return {"error": "Access denied to file"}, 403

    # Check if file is already in the target folder
    if rec.folder_id == target.id:
        return {"error": "File is already in the target folder"}, 400

    # ── new disk location ------------------------------------
    dest_dir = folder_disk_path(target, current_user.username)
    os.makedirs(dest_dir, exist_ok=True)

    new_path = os.path.join(dest_dir, rec.filename)
    
    # Check if a file with the same name already exists in destination
    if os.path.exists(new_path) and new_path != rec.path:
        return {"error": f"A file named '{rec.filename}' already exists in the destination folder"}, 400
    
    try:
        # Use shutil.move instead of os.rename for better cross-device support
        # and handling of moves between different directory levels
        import shutil
        shutil.move(rec.path, new_path)
    except OSError as e:
        return {"error": f"Failed to move file: {str(e)}"}, 500
    except Exception as e:
        return {"error": f"Unexpected error while moving file: {str(e)}"}, 500

    # ── update DB --------------------------------------------
    rec.folder_id = target.id
    rec.path      = new_path
    db.session.commit()

    return {"message": "File moved successfully"}, 200

# ────────────── Text File Edit (New Endpoints) ───────────────────────────
@app.route('/file-content/<int:file_id>', methods=['GET'])
@login_required
def get_file_content(file_id):
    file = File.query.get_or_404(file_id)
    if file.owner_id != current_user.id: # Add admin check if necessary: and not current_user.is_admin
        return {"error": "Access denied to file"}, 403

    # Basic check for text files, can be expanded (e.g., check file.mimetype)
    if not file.filename.lower().endswith(('.txt', '.md', '.py', '.js', '.json', '.yaml', '.yml', '.html', '.css')):
        return {"error": "File is not a supported editable text file type"}, 400

    try:
        # Ensure the path stored in db is the actual current path
        # (especially if versioning updates file.path)
        actual_path = file.path 
        if not os.path.exists(actual_path):
             # Fallback to version path if main path deleted or points to a version in .version
            if file.current_version:
                latest_version = FileVersion.query.filter_by(file_id=file.id, version_number=file.current_version).first()
                if latest_version and os.path.exists(latest_version.path):
                    actual_path = latest_version.path
                else:
                    return {"error": "File content not found on disk"}, 404
            else: # No versions and main path missing
                return {"error": "File content not found on disk"}, 404


        with open(actual_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({"content": content, "filename": file.filename, "mimetype": file.mimetype})
    except Exception as e:
        return {"error": f"Error reading file: {str(e)}"}, 500

@app.route('/file-content/<int:file_id>', methods=['POST'])
@login_required
def save_file_content(file_id):
    file = File.query.get_or_404(file_id)
    if file.owner_id != current_user.id: # Add admin check if necessary: and not current_user.is_admin
        return {"error": "Access denied to file"}, 403

    if not file.filename.lower().endswith(('.txt', '.md', '.py', '.js', '.json', '.yaml', '.yml', '.html', '.css')):
        return {"error": "File is not a supported editable text file type"}, 400

    data = request.json
    new_content = data.get('content')
    if new_content is None:
        return {"error": "No content provided"}, 400

    try:
        # This will overwrite the current file. 
        # TODO: Integrate with versioning if desired.
        # For versioning, you'd copy the old file to .versions, then write the new one,
        # then create a new FileVersion record and update file.current_version and file.path.
        
        actual_path = file.path
        # Ensure directory exists if it somehow got deleted (though unlikely for an existing file)
        os.makedirs(os.path.dirname(actual_path), exist_ok=True)

        with open(actual_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # Update modified time (optional, but good practice)
        file.updated_at = datetime.utcnow()
        db.session.commit()
        
        return {"message": "File saved successfully"}
    except Exception as e:
        db.session.rollback()
        return {"error": f"Error saving file: {str(e)}"}, 500

# ────────────── Rename File ──────────────────────────────────────────────
@app.route('/rename-file/<int:file_id>', methods=['POST'])
@login_required
def rename_file(file_id):
    file_to_rename = File.query.get_or_404(file_id)
    if file_to_rename.owner_id != current_user.id: # Add admin check if necessary
        return {"error": "Access denied to file"}, 403

    data = request.json
    new_filename = data.get('new_filename')

    if not new_filename or not new_filename.strip():
        return {"error": "New filename cannot be empty"}, 400
    
    new_filename = secure_filename(new_filename.strip())
    if not new_filename: # secure_filename might return empty if the name is really bad
        return {"error": "Invalid new filename"}, 400

    if new_filename == file_to_rename.filename:
        return {"message": "Filename is the same, no changes made"}, 200 # Or a 400 if preferred

    # Determine the directory of the file
    current_dir = os.path.dirname(file_to_rename.path)
    new_path = os.path.join(current_dir, new_filename)

    if os.path.exists(new_path):
        return {"error": f"A file named '{new_filename}' already exists in this folder"}, 400

    try:
        # Rename on disk
        os.rename(file_to_rename.path, new_path)

        # Update database
        file_to_rename.filename = new_filename
        file_to_rename.path = new_path
        file_to_rename.updated_at = datetime.utcnow() # Update modified time
        db.session.commit()

        # Note: This does not rename files in the .version directory.
        # Version history will still point to old version paths with old names.
        # If versions also need renaming, that would be significantly more complex.

        return {"message": "File renamed successfully", "new_filename": new_filename, "new_path": new_path}, 200
    except Exception as e:
        db.session.rollback()
        # Attempt to rollback rename if DB fails? Complex. For now, log and error.
        current_app.logger.error(f"Error renaming file {file_id}: {str(e)}")
        # If os.rename succeeded but DB failed, we have a discrepancy.
        # A more robust solution might try to rename back or use a two-phase commit pattern.
        return {"error": f"Failed to rename file: {str(e)}"}, 500

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
    root = Folder(name='Root folder', owner_id=user.id, parent_id=None)
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

# ────────────── Version Control ─────────────────────────────────────────
@app.route('/upload-version/<int:file_id>', methods=['POST'])
@login_required
def upload_version(file_id):
    f = request.files.get('file')
    comment = request.form.get('comment', '')
    
    if not f:
        return {"error": "No file provided"}, 400

    file = File.query.get_or_404(file_id)
    if file.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403

    # Create new version
    new_version_number = file.current_version + 1
    version_dir = get_version_dir(current_user.username)
    version_path = os.path.join(version_dir, f"{file_id}_v{new_version_number}_{secure_filename(f.filename)}")
    f.save(version_path)

    # Create version record
    version = FileVersion(
        file_id=file.id,
        version_number=new_version_number,
        path=version_path,
        comment=comment
    )
    
    # Update file's current version
    file.current_version = new_version_number
    file.path = version_path  # Update current file path to latest version
    
    db.session.add(version)
    db.session.commit()
    
    return {
        "message": "New version uploaded successfully",
        "version_number": new_version_number,
        "version_id": version.id
    }, 201

@app.route('/file-versions/<int:file_id>', methods=['GET'])
@login_required
def get_file_versions(file_id):
    file = File.query.get_or_404(file_id)
    if file.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403

    versions = FileVersion.query.filter_by(file_id=file_id).order_by(FileVersion.version_number.desc()).all()
    return jsonify([{
        "version_number": v.version_number,
        "uploaded_at": v.uploaded_at.isoformat(),
        "comment": v.comment,
        "is_current": v.version_number == file.current_version,
        "size": os.path.getsize(v.path) if os.path.exists(v.path) else 0
    } for v in versions])

@app.route('/restore-version/<int:file_id>/<int:version_number>', methods=['POST'])
@login_required
def restore_version(file_id, version_number):
    file = File.query.get_or_404(file_id)
    if file.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403

    version = FileVersion.query.filter_by(file_id=file_id, version_number=version_number).first_or_404()
    
    # Create new version from the restored version
    new_version_number = file.current_version + 1
    version_dir = get_version_dir(current_user.username)
    new_version_path = os.path.join(version_dir, f"{file_id}_v{new_version_number}_{secure_filename(file.filename)}")
    
    # Copy the restored version to new version
    import shutil
    shutil.copy2(version.path, new_version_path)
    
    # Create new version record
    new_version = FileVersion(
        file_id=file.id,
        version_number=new_version_number,
        path=new_version_path,
        comment=f"Restored from version {version_number}"
    )
    
    # Update file's current version and path
    file.current_version = new_version_number
    file.path = new_version_path
    
    db.session.add(new_version)
    db.session.commit()
    
    return {
        "message": f"Successfully restored version {version_number}",
        "new_version_number": new_version_number
    }

@app.route('/download-version/<int:file_id>/<int:version_number>')
@login_required
def download_version(file_id, version_number):
    file = File.query.get_or_404(file_id)
    if file.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403

    version = FileVersion.query.filter_by(file_id=file_id, version_number=version_number).first_or_404()
    
    if not os.path.exists(version.path):
        return {"error": "Version file not found"}, 404
        
    return send_from_directory(
        os.path.dirname(version.path),
        os.path.basename(version.path),
        as_attachment=True,
        download_name=f"{os.path.splitext(file.filename)[0]}_v{version_number}{os.path.splitext(file.filename)[1]}"
    )

@app.route('/delete-version/<int:file_id>/<int:version_number>', methods=['DELETE'])
@login_required
def delete_version(file_id, version_number):
    file = File.query.get_or_404(file_id)
    if file.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403

    version = FileVersion.query.filter_by(file_id=file_id, version_number=version_number).first_or_404()
    
    # Don't allow deleting the current version
    if version.version_number == file.current_version:
        return {"error": "Cannot delete current version"}, 400
        
    # Don't allow deleting the only version
    if FileVersion.query.filter_by(file_id=file_id).count() <= 1:
        return {"error": "Cannot delete the only version"}, 400
    
    try:
        os.remove(version.path)
    except FileNotFoundError:
        pass
        
    db.session.delete(version)
    db.session.commit()
    
    return {"message": f"Version {version_number} deleted successfully"}

@app.route('/restore-file/<int:file_id>', methods=['POST'])
@login_required
def restore_file(file_id):
    """
    Restore a deleted file from its latest version.
    This is useful when a file was accidentally deleted but versions still exist.
    """
    # Find the latest version
    latest_version = FileVersion.query.filter_by(file_id=file_id).order_by(FileVersion.version_number.desc()).first()
    if not latest_version:
        return {"error": "No versions found for this file"}, 404

    # Check if file still exists in database
    file = File.query.get(file_id)
    if file:
        return {"error": "File still exists, no need to restore"}, 400

    # Get the original file information from the latest version
    version_path = latest_version.path
    if not os.path.exists(version_path):
        return {"error": "Version file not found"}, 404

    # Create new file record
    new_file = File(
        filename=os.path.basename(version_path).split('_', 1)[1],  # Remove version prefix
        mimetype=latest_version.file.mimetype if latest_version.file else None,
        path=version_path,
        owner_id=current_user.id,
        folder_id=latest_version.file.folder_id if latest_version.file else None,
        current_version=latest_version.version_number
    )
    
    db.session.add(new_file)
    db.session.commit()

    return {
        "message": "File restored successfully",
        "file_id": new_file.id,
        "version_number": latest_version.version_number
    }, 201

@app.route('/cleanup-versions/<int:file_id>', methods=['POST'])
@login_required
def cleanup_versions(file_id):
    """
    Clean up old versions while keeping the current version.
    This helps manage storage space.
    """
    file = File.query.get_or_404(file_id)
    if file.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403

    # Get all versions except current
    old_versions = FileVersion.query.filter_by(file_id=file_id).filter(
        FileVersion.version_number != file.current_version
    ).all()

    deleted_count = 0
    for version in old_versions:
        try:
            if os.path.exists(version.path):
                os.remove(version.path)
            db.session.delete(version)
            deleted_count += 1
        except FileNotFoundError:
            pass

    db.session.commit()
    return {
        "message": f"Cleaned up {deleted_count} old versions",
        "current_version": file.current_version
    }

@app.route('/restore-to-version/<int:file_id>/<int:version_number>', methods=['POST'])
@login_required
def restore_to_version(file_id, version_number):
    """
    Directly restore a file to a specific version, replacing the current version.
    This is different from restore-version which creates a new version.
    """
    file = File.query.get_or_404(file_id)
    if file.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403

    # Get the target version
    target_version = FileVersion.query.filter_by(file_id=file_id, version_number=version_number).first_or_404()
    
    if not os.path.exists(target_version.path):
        return {"error": "Version file not found"}, 404

    # Create backup of current version before replacing
    current_version = FileVersion.query.filter_by(file_id=file_id, version_number=file.current_version).first()
    if current_version and os.path.exists(current_version.path):
        backup_path = os.path.join(os.path.dirname(current_version.path), 
                                 f"backup_v{current_version.version_number}_{os.path.basename(file.filename)}")
        import shutil
        shutil.copy2(current_version.path, backup_path)

    # Replace current version with target version
    try:
        import shutil
        shutil.copy2(target_version.path, file.path)
        
        # Update file's current version
        file.current_version = version_number
        
        # Update the version record's path to point to the new location
        target_version.path = file.path
        
        db.session.commit()
        
        return {
            "message": f"Successfully restored to version {version_number}",
            "current_version": version_number
        }
    except Exception as e:
        # If something goes wrong, try to restore from backup
        if 'backup_path' in locals() and os.path.exists(backup_path):
            shutil.copy2(backup_path, file.path)
        db.session.rollback()
        return {"error": f"Failed to restore version: {str(e)}"}, 500

@app.route('/compare-versions/<int:file_id>/<int:version1>/<int:version2>', methods=['GET'])
@login_required
def compare_versions(file_id, version1, version2):
    """
    Compare two versions of a file and return their differences.
    This is useful for text files. For binary files, it will return basic metadata comparison.
    """
    file = File.query.get_or_404(file_id)
    if file.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403

    v1 = FileVersion.query.filter_by(file_id=file_id, version_number=version1).first_or_404()
    v2 = FileVersion.query.filter_by(file_id=file_id, version_number=version2).first_or_404()

    if not os.path.exists(v1.path) or not os.path.exists(v2.path):
        return {"error": "One or both version files not found"}, 404

    # Basic metadata comparison
    comparison = {
        "version1": {
            "number": v1.version_number,
            "uploaded_at": v1.uploaded_at.isoformat(),
            "comment": v1.comment,
            "size": os.path.getsize(v1.path)
        },
        "version2": {
            "number": v2.version_number,
            "uploaded_at": v2.uploaded_at.isoformat(),
            "comment": v2.comment,
            "size": os.path.getsize(v2.path)
        }
    }

    # For text files, try to show content differences
    if file.mimetype and file.mimetype.startswith('text/'):
        try:
            with open(v1.path, 'r') as f1, open(v2.path, 'r') as f2:
                content1 = f1.read()
                content2 = f2.read()
                
                # Simple line-by-line comparison
                lines1 = content1.splitlines()
                lines2 = content2.splitlines()
                
                comparison["text_differences"] = {
                    "total_lines_v1": len(lines1),
                    "total_lines_v2": len(lines2),
                    "different_lines": []
                }
                
                # Compare lines and collect differences
                for i, (line1, line2) in enumerate(zip(lines1, lines2)):
                    if line1 != line2:
                        comparison["text_differences"]["different_lines"].append({
                            "line_number": i + 1,
                            "version1": line1,
                            "version2": line2
                        })
                
                # Handle different length files
                if len(lines1) != len(lines2):
                    comparison["text_differences"]["length_difference"] = {
                        "v1_extra_lines": len(lines1) - len(lines2) if len(lines1) > len(lines2) else 0,
                        "v2_extra_lines": len(lines2) - len(lines1) if len(lines2) > len(lines1) else 0
                    }
        except Exception as e:
            comparison["text_comparison_error"] = str(e)

    return jsonify(comparison)

# ────────────── Bootstrapping ────────────────────────────────────────────
def create_default_test_user():
    """Create a default test user if it doesn't exist"""
    existing_user = User.query.filter_by(username='test').first()
    if not existing_user:
        test_user = User(username='test', email='test@example.com')
        test_user.set_password('test')
        db.session.add(test_user)
        db.session.flush()  # Get the user ID
        
        # Create root folder for test user
        root_folder = Folder(name='Root folder', owner_id=test_user.id, parent_id=None)
        db.session.add(root_folder)
        db.session.commit()
        
        # Create user directory on disk
        user_dir = os.path.join(Config.UPLOAD_FOLDER, 'test')
        os.makedirs(user_dir, exist_ok=True)
        
        # Create version directory for the user
        version_dir = os.path.join(user_dir, '.version')
        os.makedirs(version_dir, exist_ok=True)
        
        print("✅ Created default test user (username: test, password: test)")
    else:
        print("ℹ️  Test user already exists")

if __name__ == '__main__':
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    app.secret_key = os.getenv("SECRET_KEY", "dev-secret")

    for i in range(10):
        try:
            with app.app_context():
                db.create_all()
                print("✅ tables:", inspect(db.engine).get_table_names())
                
                # Create default test user after tables are created
                create_default_test_user()
                break
        except OperationalError:
            print("⏳ waiting for MySQL…"); time.sleep(3)
    else:
        print("❌ DB not reachable"); exit(1)

    app.run(host='0.0.0.0', port=5001)