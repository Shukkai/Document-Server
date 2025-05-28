#!/usr/bin/env python3
"""
Migration script to add version tracking fields to DocumentReview table
"""

from app import app, db
from models import DocumentReview

def migrate_review_versions():
    """Add version tracking fields to DocumentReview table"""
    with app.app_context():
        try:
            # Check if columns already exist
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('document_review')]
            
            if 'original_version' not in columns:
                print("Adding original_version column...")
                db.engine.execute('ALTER TABLE document_review ADD COLUMN original_version INTEGER')
            
            if 'modified_version' not in columns:
                print("Adding modified_version column...")
                db.engine.execute('ALTER TABLE document_review ADD COLUMN modified_version INTEGER')
            
            print("Migration completed successfully!")
            
        except Exception as e:
            print(f"Migration failed: {e}")
            return False
    
    return True

if __name__ == "__main__":
    migrate_review_versions() 