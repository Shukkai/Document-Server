"""
Folder routes for Document Center
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
import os
import shutil

from ..models import db, File, Folder
from ..utils.file_utils import folder_disk_path
from ..utils.cache import cache, invalidate_cache, CacheManager

bp = Blueprint('folders', __name__)


@bp.route('/folders', methods=['GET'])
@login_required
@cache(expire=60, key_prefix="folders")  # Cache for 1 minute
def get_folders():
    def ser(folder: Folder):
        return {
            "id": folder.id, "name": folder.name,
            "parent_id": folder.parent_id,
            "files": [
                {
                    "id": f.id, "name": f.filename,
                    "mimetype": f.mimetype,
                    "uploaded_at": f.uploaded_at.isoformat(),
                    "is_under_review": f.is_under_review,
                    "is_published": f.is_published,
                    "active_review": {
                        "id": f.get_active_review().id,
                        "reviewer": f.get_active_review().reviewer.username,
                        "requested_at": f.get_active_review().requested_at.isoformat()
                    } if f.get_active_review() else None
                } for f in folder.files if f.owner_id == current_user.id
            ],
            "children": [ser(ch) for ch in folder.subfolders if ch.owner_id == current_user.id]
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


@bp.route('/public-files', methods=['GET'])
@login_required
@cache(expire=300, key_prefix="public_files")  # Cache for 5 minutes
def get_all_public_files():
    all_publics = File.query.filter_by(is_published=True).all()

    files_data = []
    for file in all_publics:
        files_data.append({
            "id": file.id,
            "name": file.filename,
            "mimetype": file.mimetype,
            "path": file.path,
            "uploaded_at": file.uploaded_at.isoformat(),
            "is_under_review": file.is_under_review,
            "is_published": file.is_published,
            "current_version": file.current_version,
            # "active_review": {
            #     "id": file.get_active_review().id if file.get_active_review() else None,
            #     "reviewer": file.get_active_review().reviewer.username if file.get_active_review() else None,
            #     "requested_at": file.get_active_review().requested_at.isoformat() if file.get_active_review() else None
            # }
        })

    return jsonify({
        "pfiles": files_data,
    })


@bp.route('/folders', methods=['POST'])
@login_required
@invalidate_cache(pattern="folders:*")  # Invalidate folder cache when creating new folder
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


@bp.route('/folders/<int:fid>', methods=['DELETE'])
@login_required
@invalidate_cache(pattern="folders:*")  # Invalidate folder cache when deleting folder
def delete_folder(fid):
    fld = Folder.query.get_or_404(fid)
    if fld.owner_id != current_user.id:
        return {"error": "Access denied"}, 403
    if fld.parent_id is None:
        return {"error": "Cannot delete root folder"}, 400
    
    current_app.logger.info(f"Deleting folder {fld.id} '{fld.name}' with all contents")
    
    try:
        # Recursively delete all files and subfolders
        def delete_folder_recursive(folder):
            """Recursively delete a folder and all its contents"""
            current_app.logger.info(f"Processing folder: {folder.name} (ID: {folder.id})")
            
            # Delete all files in this folder
            for file in folder.files:
                try:
                    current_app.logger.info(f"Deleting file: {file.filename} at {file.path}")
                    if os.path.exists(file.path):
                        os.remove(file.path)
                        current_app.logger.info(f"Successfully deleted file from disk: {file.path}")
                    else:
                        current_app.logger.warning(f"File not found on disk: {file.path}")
                    
                    # Delete file versions
                    from ..models import FileVersion
                    versions = FileVersion.query.filter_by(file_id=file.id).all()
                    for version in versions:
                        try:
                            if os.path.exists(version.path):
                                os.remove(version.path)
                                current_app.logger.info(f"Deleted version file: {version.path}")
                        except Exception as e:
                            current_app.logger.error(f"Error deleting version file {version.path}: {e}")
                        db.session.delete(version)
                    
                    db.session.delete(file)
                    current_app.logger.info(f"Deleted file record: {file.filename}")
                    
                except Exception as e:
                    current_app.logger.error(f"Error deleting file {file.id}: {str(e)}")
            
            # Recursively delete all subfolders
            for subfolder in folder.subfolders:
                delete_folder_recursive(subfolder)
            
            # Delete the physical folder
            folder_path = folder_disk_path(folder, current_user.username)
            if os.path.exists(folder_path):
                try:
                    shutil.rmtree(folder_path)
                    current_app.logger.info(f"Successfully deleted physical folder: {folder_path}")
                except Exception as e:
                    current_app.logger.error(f"Error deleting physical folder {folder_path}: {e}")
            else:
                current_app.logger.warning(f"Physical folder not found: {folder_path}")
            
            # Delete from database
            db.session.delete(folder)
            current_app.logger.info(f"Deleted folder record: {folder.name}")
        
        # Start recursive deletion
        delete_folder_recursive(fld)
        
        # Commit all changes
        db.session.commit()
        current_app.logger.info(f"Successfully deleted folder {fld.id} '{fld.name}' and all contents")
        
        return {"message": "Folder deleted successfully"}
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting folder {fld.id}: {str(e)}")
        return {"error": f"Failed to delete folder: {str(e)}"}, 500


@bp.route('/move-file', methods=['POST'])
@login_required
@invalidate_cache(pattern="folders:*")  # Invalidate folder cache when moving files
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


@bp.route('/cleanup-orphaned-files', methods=['POST'])
@login_required
def cleanup_orphaned_files():
    """Clean up orphaned files and folders that exist on disk but not in the database"""
    if not current_user.is_admin:
        return {"error": "Admin access required"}, 403
    
    current_app.logger.info("Starting orphaned files cleanup")
    
    try:
        from ..config import Config
        upload_folder = Config.UPLOAD_FOLDER
        
        if not os.path.exists(upload_folder):
            return {"message": "Upload folder does not exist"}, 404
        
        cleaned_files = 0
        cleaned_folders = 0
        
        # Get all files in database
        db_files = set()
        for file in File.query.all():
            if os.path.exists(file.path):
                db_files.add(file.path)
        
        # Get all version files in database
        db_versions = set()
        from ..models import FileVersion
        for version in FileVersion.query.all():
            if os.path.exists(version.path):
                db_versions.add(version.path)
        
        # Walk through upload folder and find orphaned files
        for root, dirs, files in os.walk(upload_folder):
            # Check files
            for file in files:
                file_path = os.path.join(root, file)
                if file_path not in db_files and file_path not in db_versions:
                    try:
                        os.remove(file_path)
                        current_app.logger.info(f"Cleaned orphaned file: {file_path}")
                        cleaned_files += 1
                    except Exception as e:
                        current_app.logger.error(f"Error cleaning orphaned file {file_path}: {e}")
            
            # Check folders (but skip .version folders)
            for dir_name in dirs:
                if dir_name == '.version':
                    continue
                    
                dir_path = os.path.join(root, dir_name)
                # Check if this folder exists in database
                folder_exists = False
                for folder in Folder.query.all():
                    folder_disk_path_val = folder_disk_path(folder, folder.owner.username)
                    if folder_disk_path_val == dir_path:
                        folder_exists = True
                        break
                
                if not folder_exists:
                    try:
                        shutil.rmtree(dir_path)
                        current_app.logger.info(f"Cleaned orphaned folder: {dir_path}")
                        cleaned_folders += 1
                    except Exception as e:
                        current_app.logger.error(f"Error cleaning orphaned folder {dir_path}: {e}")
        
        current_app.logger.info(f"Cleanup completed: {cleaned_files} files, {cleaned_folders} folders")
        
        return {
            "message": "Cleanup completed successfully",
            "cleaned_files": cleaned_files,
            "cleaned_folders": cleaned_folders
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Error during cleanup: {str(e)}")
        return {"error": f"Cleanup failed: {str(e)}"}, 500 