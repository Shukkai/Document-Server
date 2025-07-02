"""
File routes for Document Center
"""

from flask import Blueprint, request, jsonify, send_from_directory, current_app, send_file, Response
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import shutil

from ..models import db, File, Folder, FileVersion
from ..utils.file_utils import folder_disk_path, get_version_dir, get_next_version_number, get_content_for_version

bp = Blueprint('files', __name__)


@bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    f = request.files.get('file')
    folder_id = request.form.get('folder_id', type=int)
    if not f:
        return {"error": "No file provided"}, 400

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
    os.makedirs(version_dir, exist_ok=True)
    version_path = os.path.join(version_dir, f"{rec.id}_v1_{secure_filename(f.filename)}")
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


@bp.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    rec = File.query.get_or_404(file_id)
    if rec.is_published == False and rec.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403
    
    # Debug logging
    current_app.logger.info(f"Download request for file {file_id}: {rec.filename}")
    current_app.logger.info(f"File path: {rec.path}")
    current_app.logger.info(f"Directory: {os.path.dirname(rec.path)}")
    current_app.logger.info(f"Basename: {os.path.basename(rec.path)}")
    current_app.logger.info(f"File exists: {os.path.exists(rec.path)}")
    
    if not os.path.exists(rec.path):
        current_app.logger.error(f"File not found on disk: {rec.path}")
        return {"error": "File not found on disk"}, 404
    
    try:
        # Get file size
        file_size = os.path.getsize(rec.path)
        
        # Force download by setting proper headers
        response = send_file(
            rec.path,
            as_attachment=True,
            download_name=rec.filename,
            mimetype=rec.mimetype
        )
        
        # Add additional headers to force download
        response.headers['Content-Disposition'] = f'attachment; filename="{rec.filename}"'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['Content-Length'] = str(file_size)
        
        # Ensure proper content type for binary files
        if rec.mimetype and rec.mimetype.startswith('image/'):
            response.headers['Content-Type'] = rec.mimetype
        
        # Add CORS headers if needed
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Error serving file {file_id}: {str(e)}")
        return {"error": "Failed to serve file"}, 500


@bp.route('/delete/<int:file_id>', methods=['DELETE'])
@login_required
def delete_file(file_id):
    rec = File.query.get_or_404(file_id)
    if rec.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403

    current_app.logger.info(f"Deleting file {file_id}: {rec.filename}")

    try:
        # Delete the main file from disk
        if os.path.exists(rec.path):
            os.remove(rec.path)
            current_app.logger.info(f"Deleted main file from disk: {rec.path}")
        else:
            current_app.logger.warning(f"Main file not found on disk: {rec.path}")
        
        # Delete all version files
        versions = FileVersion.query.filter_by(file_id=file_id).all()
        for version in versions:
            try:
                if os.path.exists(version.path):
                    os.remove(version.path)
                    current_app.logger.info(f"Deleted version file: {version.path}")
                else:
                    current_app.logger.warning(f"Version file not found on disk: {version.path}")
            except Exception as e:
                current_app.logger.error(f"Error deleting version file {version.path}: {e}")
            db.session.delete(version)
        
        # Delete the file record from database
        db.session.delete(rec)
        db.session.commit()
        
        current_app.logger.info(f"Successfully deleted file {file_id} and all versions")
        
        return {
            "message": "File deleted successfully.",
            "file_id": file_id
        }, 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting file {file_id}: {str(e)}")
        return {"error": "Failed to delete file"}, 500


@bp.route('/list-deleted-files', methods=['GET'])
@login_required
def list_deleted_files():
    """
    List all files that have been deleted but still have version history.
    This helps users find files they might want to restore.
    """
    # Find all version records that don't have an associated file
    versions = db.session.query(FileVersion).outerjoin(File).filter(File.id == None).all()
    
    # Filter versions to only include those belonging to current user
    user_username = current_user.username
    user_versions = [v for v in versions if f"/{user_username}/" in v.path or v.path.startswith(f"{user_username}/")]
    
    # Group versions by file_id to get the latest version for each deleted file
    deleted_files = {}
    for version in user_versions:
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


@bp.route('/permanently-delete/<int:file_id>', methods=['DELETE'])
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


@bp.route('/file-content/<int:file_id>', methods=['GET'])
@login_required
def get_file_content(file_id):
    """Get the content of a file"""
    file = File.query.get_or_404(file_id)
    
    # Check access permissions
    if not file.is_published and file.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403
    
    try:
        if os.path.exists(file.path):
            with open(file.path, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({
                "content": content,
                "filename": file.filename,
                "current_version": file.current_version
            })
        else:
            return {"error": "File not found on disk"}, 404
    except Exception as e:
        current_app.logger.error(f"Error reading file {file_id}: {str(e)}")
        return {"error": "Failed to read file"}, 500


@bp.route('/file-content/<int:file_id>', methods=['POST'])
@login_required
def save_file_content(file_id):
    """Save content to a file and create a new version"""
    file = File.query.get_or_404(file_id)
    
    if file.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403
    
    data = request.get_json()
    if not data or 'content' not in data:
        return {"error": "Content is required"}, 400
    
    try:
        # Save the new content to the file
        with open(file.path, 'w', encoding='utf-8') as f:
            f.write(data['content'])
        
        # Create a new version
        new_version_number = get_next_version_number(file_id)
        version_dir = get_version_dir(current_user.username)
        os.makedirs(version_dir, exist_ok=True)
        
        version_path = os.path.join(version_dir, f"{file_id}_v{new_version_number}_{secure_filename(file.filename)}")
        shutil.copy2(file.path, version_path)
        
        version = FileVersion(
            file_id=file_id,
            version_number=new_version_number,
            path=version_path,
            comment=data.get('comment', f'Version {new_version_number}')
        )
        db.session.add(version)
        
        # Update file's current version
        file.current_version = new_version_number
        db.session.commit()
        
        return {
            "message": "File saved successfully",
            "new_version": new_version_number
        }, 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error saving file {file_id}: {str(e)}")
        return {"error": "Failed to save file"}, 500


@bp.route('/rename-file/<int:file_id>', methods=['POST'])
@login_required
def rename_file(file_id):
    """Rename a file"""
    file = File.query.get_or_404(file_id)
    
    if file.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403
    
    data = request.get_json()
    new_name = data.get('new_name')
    if not new_name:
        return {"error": "New name is required"}, 400
    
    try:
        # Check if file with new name already exists in the same folder
        existing_file = File.query.filter_by(
            filename=new_name,
            folder_id=file.folder_id,
            owner_id=current_user.id
        ).first()
        
        if existing_file and existing_file.id != file_id:
            return {"error": "A file with this name already exists in this folder"}, 400
        
        # Rename the file on disk
        old_path = file.path
        new_path = os.path.join(os.path.dirname(old_path), secure_filename(new_name))
        
        if os.path.exists(old_path):
            os.rename(old_path, new_path)
        
        # Update the file record
        file.filename = new_name
        file.path = new_path
        
        # Update all version paths
        versions = FileVersion.query.filter_by(file_id=file_id).all()
        for version in versions:
            old_version_path = version.path
            new_version_path = os.path.join(
                os.path.dirname(old_version_path),
                f"{file_id}_v{version.version_number}_{secure_filename(new_name)}"
            )
            
            if os.path.exists(old_version_path):
                os.rename(old_version_path, new_version_path)
            
            version.path = new_version_path
        
        db.session.commit()
        return {"message": "File renamed successfully"}, 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error renaming file {file_id}: {str(e)}")
        return {"error": "Failed to rename file"}, 500


# Version management routes
@bp.route('/upload-version/<int:file_id>', methods=['POST'])
@login_required
def upload_version(file_id):
    """Upload a new version of a file"""
    file = File.query.get_or_404(file_id)
    
    if file.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403
    
    f = request.files.get('file')
    if not f:
        return {"error": "No file provided"}, 400
    
    try:
        # Save the new file content
        with open(file.path, 'wb') as f_write:
            f.save(f_write)
        
        # Create a new version record
        new_version_number = get_next_version_number(file_id)
        version_dir = get_version_dir(current_user.username)
        os.makedirs(version_dir, exist_ok=True)
        
        version_path = os.path.join(version_dir, f"{file_id}_v{new_version_number}_{secure_filename(file.filename)}")
        shutil.copy2(file.path, version_path)
        
        version = FileVersion(
            file_id=file_id,
            version_number=new_version_number,
            path=version_path,
            comment=request.form.get('comment', f'Version {new_version_number}')
        )
        db.session.add(version)
        
        # Update file's current version
        file.current_version = new_version_number
        db.session.commit()
        
        return {
            "message": "Version uploaded successfully",
            "new_version": new_version_number
        }, 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error uploading version for file {file_id}: {str(e)}")
        return {"error": "Failed to upload version"}, 500


@bp.route('/file-versions/<int:file_id>', methods=['GET'])
@login_required
def get_file_versions(file_id):
    """Get all versions of a file"""
    file = File.query.get_or_404(file_id)
    
    if not file.is_published and file.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403
    
    versions = FileVersion.query.filter_by(file_id=file_id).order_by(FileVersion.version_number.desc()).all()
    
    return jsonify([{
        "version_number": v.version_number,
        "comment": v.comment,
        "uploaded_at": v.uploaded_at.isoformat(),
        "size": os.path.getsize(v.path) if os.path.exists(v.path) else 0
    } for v in versions])


@bp.route('/restore-version/<int:file_id>/<int:version_number>', methods=['POST'])
@login_required
def restore_version(file_id, version_number):
    """Restore a file to a specific version"""
    file = File.query.get_or_404(file_id)
    
    if file.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403
    
    version = FileVersion.query.filter_by(file_id=file_id, version_number=version_number).first()
    if not version:
        return {"error": "Version not found"}, 404
    
    try:
        # Restore the file content from the version
        if os.path.exists(version.path):
            shutil.copy2(version.path, file.path)
        else:
            return {"error": "Version file not found on disk"}, 404
        
        # Create a new version record for this restoration
        new_version_number = get_next_version_number(file_id)
        version_dir = get_version_dir(current_user.username)
        os.makedirs(version_dir, exist_ok=True)
        
        new_version_path = os.path.join(version_dir, f"{file_id}_v{new_version_number}_{secure_filename(file.filename)}")
        shutil.copy2(file.path, new_version_path)
        
        new_version = FileVersion(
            file_id=file_id,
            version_number=new_version_number,
            path=new_version_path,
            comment=f"Restored from version {version_number}"
        )
        db.session.add(new_version)
        
        # Update file's current version
        file.current_version = new_version_number
        db.session.commit()
        
        return {
            "message": f"File restored to version {version_number}",
            "new_version": new_version_number
        }, 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error restoring version {version_number} for file {file_id}: {str(e)}")
        return {"error": "Failed to restore version"}, 500


@bp.route('/download-version/<int:file_id>/<int:version_number>')
@login_required
def download_version(file_id, version_number):
    """Download a specific version of a file"""
    file = File.query.get_or_404(file_id)
    
    if not file.is_published and file.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403
    
    version = FileVersion.query.filter_by(file_id=file_id, version_number=version_number).first()
    if not version:
        return {"error": "Version not found"}, 404
    
    if not os.path.exists(version.path):
        return {"error": "Version file not found on disk"}, 404
    
    try:
        # Get file size
        file_size = os.path.getsize(version.path)
        
        # Force download by setting proper headers
        # Extract original filename from version path (remove version prefix)
        version_filename = os.path.basename(version.path)
        if '_v' in version_filename:
            original_filename = version_filename.split('_v', 1)[1].split('_', 1)[1] if '_v' in version_filename else version_filename
        else:
            original_filename = version_filename
        
        response = send_file(
            version.path,
            as_attachment=True,
            download_name=f"{original_filename} (v{version_number})",
            mimetype=file.mimetype
        )
        
        # Add additional headers to force download
        response.headers['Content-Disposition'] = f'attachment; filename="{original_filename} (v{version_number})"'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['Content-Length'] = str(file_size)
        
        # Ensure proper content type for binary files
        if file.mimetype and file.mimetype.startswith('image/'):
            response.headers['Content-Type'] = file.mimetype
        
        # Add CORS headers if needed
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Error serving version {version_number} for file {file_id}: {str(e)}")
        return {"error": "Failed to serve file version"}, 500


@bp.route('/version-content/<int:file_id>/<int:version_number>', methods=['GET'])
@login_required
def get_version_content(file_id, version_number):
    """Get the content of a specific version of a file"""
    file = File.query.get_or_404(file_id)
    
    if not file.is_published and file.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403
    
    content = get_content_for_version(file, version_number)
    
    return jsonify({
        "content": content,
        "version_number": version_number,
        "filename": file.filename
    })


@bp.route('/delete-version/<int:file_id>/<int:version_number>', methods=['DELETE'])
@login_required
def delete_version(file_id, version_number):
    """Delete a specific version of a file"""
    file = File.query.get_or_404(file_id)
    
    if file.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403
    
    version = FileVersion.query.filter_by(file_id=file_id, version_number=version_number).first()
    if not version:
        return {"error": "Version not found"}, 404
    
    # Don't allow deletion of the current version
    if version_number == file.current_version:
        return {"error": "Cannot delete the current version"}, 400
    
    try:
        # Delete the version file from disk
        if os.path.exists(version.path):
            os.remove(version.path)
        
        # Delete the version record
        db.session.delete(version)
        db.session.commit()
        
        return {"message": f"Version {version_number} deleted successfully"}, 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting version {version_number} for file {file_id}: {str(e)}")
        return {"error": "Failed to delete version"}, 500


@bp.route('/restore-file/<int:file_id>', methods=['POST'])
@login_required
def restore_file(file_id):
    """Restore a deleted file from its latest version"""
    # Find the latest version for this file
    latest_version = db.session.query(FileVersion).filter_by(file_id=file_id).order_by(FileVersion.version_number.desc()).first()
    
    if not latest_version:
        return {"error": "No versions found for this file"}, 404
    
    # Check if the version belongs to the current user
    user_username = current_user.username
    if f"/{user_username}/" not in latest_version.path and not latest_version.path.startswith(f"{user_username}/"):
        return {"error": "Access denied"}, 403
    
    try:
        # Create a new file record
        filename = os.path.basename(latest_version.path).split('_', 1)[1]  # Remove version prefix
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.username, filename)
        
        # Copy the version file to the main uploads directory
        if os.path.exists(latest_version.path):
            shutil.copy2(latest_version.path, file_path)
        else:
            return {"error": "Version file not found on disk"}, 404
        
        # Create the file record
        file = File(
            filename=filename,
            mimetype='text/plain',  # Default mimetype
            path=file_path,
            owner_id=current_user.id,
            current_version=latest_version.version_number
        )
        db.session.add(file)
        db.session.flush()  # Get the file ID
        
        # Update the version record to point to the new file
        latest_version.file_id = file.id
        db.session.commit()
        
        return {
            "message": "File restored successfully",
            "file_id": file.id
        }, 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error restoring file {file_id}: {str(e)}")
        return {"error": "Failed to restore file"}, 500


@bp.route('/cleanup-versions/<int:file_id>', methods=['POST'])
@login_required
def cleanup_versions(file_id):
    """Clean up old versions of a file, keeping only the current version"""
    file = File.query.get_or_404(file_id)
    
    if file.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403
    
    try:
        # Get all versions except the current one
        old_versions = FileVersion.query.filter_by(file_id=file_id).filter(
            FileVersion.version_number != file.current_version
        ).all()
        
        deleted_count = 0
        for version in old_versions:
            # Delete the version file from disk
            if os.path.exists(version.path):
                os.remove(version.path)
            
            # Delete the version record
            db.session.delete(version)
            deleted_count += 1
        
        db.session.commit()
        
        return {
            "message": f"Cleaned up {deleted_count} old versions",
            "deleted_count": deleted_count
        }, 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error cleaning up versions for file {file_id}: {str(e)}")
        return {"error": "Failed to cleanup versions"}, 500


@bp.route('/restore-to-version/<int:file_id>/<int:version_number>', methods=['POST'])
@login_required
def restore_to_version(file_id, version_number):
    """Restore a file to a specific version and delete all newer versions"""
    file = File.query.get_or_404(file_id)
    
    if file.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403
    
    target_version = FileVersion.query.filter_by(file_id=file_id, version_number=version_number).first()
    if not target_version:
        return {"error": "Target version not found"}, 404
    
    try:
        # Restore the file content from the target version
        if os.path.exists(target_version.path):
            shutil.copy2(target_version.path, file.path)
        else:
            return {"error": "Target version file not found on disk"}, 404
        
        # Delete all versions newer than the target version
        newer_versions = FileVersion.query.filter_by(file_id=file_id).filter(
            FileVersion.version_number > version_number
        ).all()
        
        deleted_count = 0
        for version in newer_versions:
            # Delete the version file from disk
            if os.path.exists(version.path):
                os.remove(version.path)
            
            # Delete the version record
            db.session.delete(version)
            deleted_count += 1
        
        # Update file's current version
        file.current_version = version_number
        db.session.commit()
        
        return {
            "message": f"File restored to version {version_number} and {deleted_count} newer versions deleted",
            "current_version": version_number,
            "deleted_count": deleted_count
        }, 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error restoring to version {version_number} for file {file_id}: {str(e)}")
        return {"error": "Failed to restore to version"}, 500


@bp.route('/compare-versions/<int:file_id>/<int:version1>/<int:version2>', methods=['GET'])
@login_required
def compare_versions(file_id, version1, version2):
    """Compare two versions of a file"""
    file = File.query.get_or_404(file_id)
    
    if not file.is_published and file.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403
    
    # Get the content of both versions
    content1 = get_content_for_version(file, version1)
    content2 = get_content_for_version(file, version2)
    
    # Simple line-by-line comparison
    lines1 = content1.splitlines()
    lines2 = content2.splitlines()
    
    # Find differences
    differences = []
    max_lines = max(len(lines1), len(lines2))
    
    for i in range(max_lines):
        line1 = lines1[i] if i < len(lines1) else ""
        line2 = lines2[i] if i < len(lines2) else ""
        
        if line1 != line2:
            differences.append({
                "line_number": i + 1,
                "version1": line1,
                "version2": line2
            })
    
    return jsonify({
        "file_id": file_id,
        "version1": version1,
        "version2": version2,
        "differences": differences,
        "total_differences": len(differences)
    })


@bp.route('/preview/<int:file_id>')
@login_required
def preview_file(file_id):
    """Preview a file for display in browser (no download)"""
    rec = File.query.get_or_404(file_id)
    if rec.is_published == False and rec.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403
    
    if not os.path.exists(rec.path):
        current_app.logger.error(f"File not found on disk: {rec.path}")
        return {"error": "File not found on disk"}, 404
    
    # Serve file for display (no download headers)
    return send_file(
        rec.path,
        mimetype=rec.mimetype
    )


@bp.route('/preview-version/<int:file_id>/<int:version_number>')
@login_required
def preview_version(file_id, version_number):
    """Preview a specific version of a file for display in browser (no download)"""
    file = File.query.get_or_404(file_id)
    
    if not file.is_published and file.owner_id != current_user.id and not current_user.is_admin:
        return {"error": "Access denied"}, 403
    
    version = FileVersion.query.filter_by(file_id=file_id, version_number=version_number).first()
    if not version:
        return {"error": "Version not found"}, 404
    
    if not os.path.exists(version.path):
        return {"error": "Version file not found on disk"}, 404
    
    # Serve version file for display (no download headers)
    return send_file(
        version.path,
        mimetype=file.mimetype
    ) 