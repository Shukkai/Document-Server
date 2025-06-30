"""
Admin routes for Document Center
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from ..models import db, User, Folder

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route('/list-users', methods=['GET'])
@login_required
def admin_list_users():
    if not current_user.is_admin:
        return {"error": "Admin access required"}, 403
    users = User.query.filter(User.id != current_user.id).all()  # Exclude current admin
    return jsonify([{
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "grade": user.grade,
        "created_at": user.created_at.isoformat() if user.created_at else None
    } for user in users])


@bp.route('/user-files/<int:target_user_id>', methods=['GET'])
@login_required
def admin_get_user_files(target_user_id):
    if not current_user.is_admin:
        return {"error": "Admin access required"}, 403

    target_user = User.query.get(target_user_id)
    if not target_user:
        return {"error": "Target user not found"}, 404

    # Adjusted serialization function to work with target_user context
    def ser_admin(folder: Folder, for_user: User):
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
                    "current_version": f.current_version,  # Add current_version for admin view
                    "owner_id": f.owner_id,  # Explicitly include owner_id
                    "active_review": {
                        "id": f.get_active_review().id,
                        "reviewer": f.get_active_review().reviewer.username,
                        "requested_at": f.get_active_review().requested_at.isoformat()
                    } if f.get_active_review() else None
                } for f in folder.files if f.owner_id == for_user.id  # Filter by target user
            ],
            "children": [ser_admin(ch, for_user) for ch in folder.subfolders if ch.owner_id == for_user.id]  # Filter by target user
        }
    
    # Fetch root folder for the target user
    root_folder_target_user = Folder.query.filter_by(owner_id=target_user.id, parent_id=None).first()
    
    if not root_folder_target_user:
        # If target user has no root folder (e.g., new user, or some issue)
        # Return an empty structure for their files.
        return jsonify({
            "tree": {"id": None, "name": f"{target_user.username}'s Files (Root)", "files": [], "children": []},
            "target_user": {"id": target_user.id, "username": target_user.username}
        })

    folder_tree = ser_admin(root_folder_target_user, target_user)
    
    # We don't need flat_folders for this admin view of another user's files, 
    # as moving files between users is not part of this feature yet.
    
    return jsonify({
        "tree": folder_tree,
        "target_user": {"id": target_user.id, "username": target_user.username}
    }) 