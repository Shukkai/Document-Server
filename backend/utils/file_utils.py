"""
File utility functions for Document Center
"""

import os
from typing import Optional
from flask import current_app
from ..models import Folder


def folder_disk_path(folder: Optional[Folder], username: str) -> str:
    """
    Build uploads/<username>/… path for *folder*.
    If *folder* is None ⇒ returns user root folder.
    """
    if not folder or folder.parent_id is None:
        return os.path.join(current_app.config['UPLOAD_FOLDER'], username)
    
    # Build the full path hierarchy recursively
    path_parts = []
    current = folder
    
    while current and current.parent_id is not None:
        path_parts.append(current.name)
        current = Folder.query.get(current.parent_id)
    
    path_parts.reverse()  # Reverse to get correct order
    return os.path.join(current_app.config['UPLOAD_FOLDER'], username, *path_parts)


def get_version_dir(username: str) -> str:
    """Returns the .version directory for a user"""
    from ..config import Config
    return os.path.join(Config.UPLOAD_FOLDER, username, '.version')


def get_next_version_number(file_id: int) -> int:
    """Get the next available version number for a file"""
    from ..models import db, FileVersion
    highest_version = db.session.query(db.func.max(FileVersion.version_number)).filter_by(file_id=file_id).scalar()
    return (highest_version or 0) + 1


def get_content_for_version(file_obj, version_number_to_fetch: Optional[int]) -> str:
    """Fetches the content for a given file and version number.
    Assumes FileVersion(N).path stores the actual content of version N.
    """
    from ..models import db, FileVersion
    
    if version_number_to_fetch is None:
        current_app.logger.info(f"Requested version is None for file {file_obj.id}. Returning empty content.")
        return ""

    # Ensure file_obj is associated with the current session
    if file_obj not in db.session:
        file_obj = db.session.merge(file_obj)

    fv_record = db.session.query(FileVersion).filter_by(file_id=file_obj.id, version_number=version_number_to_fetch).first()

    if not fv_record:
        current_app.logger.warning(f"FileVersion record not found for file {file_obj.id}, version {version_number_to_fetch}.")
        return ""
        
    content_path = fv_record.path
    
    if content_path and os.path.exists(content_path):
        try:
            with open(content_path, 'r', encoding='utf-8') as f:
                content = f.read()
            current_app.logger.info(f"Successfully read content for file {file_obj.id} V{version_number_to_fetch} from {content_path}. Length: {len(content)}")
            return content
        except Exception as e:
            current_app.logger.error(f"Error reading content for file {file_obj.id} V{version_number_to_fetch} from {content_path}: {e}", exc_info=True)
            return ""
    else:
        current_app.logger.warning(f"Content path for file {file_obj.id} V{version_number_to_fetch} not found or does not exist. Path: {content_path}")
        return "" 