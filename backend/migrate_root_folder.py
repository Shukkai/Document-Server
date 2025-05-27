#!/usr/bin/env python3
"""
Migration script to rename root folders from username to "Root folder"
"""
import os
import sys
from flask import Flask
from models import db, Folder, User
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def migrate_root_folders():
    """Update all root folders to be named 'Root folder' instead of username"""
    app = create_app()
    
    with app.app_context():
        # Find all root folders (parent_id is None)
        root_folders = Folder.query.filter_by(parent_id=None).all()
        
        updated_count = 0
        for folder in root_folders:
            if folder.name != 'Root folder':
                old_name = folder.name
                folder.name = 'Root folder'
                updated_count += 1
                print(f"Updated root folder: '{old_name}' -> 'Root folder' (ID: {folder.id})")
        
        if updated_count > 0:
            db.session.commit()
            print(f"✅ Successfully updated {updated_count} root folder(s)")
        else:
            print("ℹ️  No root folders needed updating")

if __name__ == '__main__':
    migrate_root_folders() 