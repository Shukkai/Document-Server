from app import app, db
from models import User, File, Folder

def check_test_user():
    with app.app_context():
        # Find test user
        test_user = User.query.filter_by(username='test').first()
        if not test_user:
            print("❌ Test user not found")
            return
        
        print(f"✅ Test user found: ID={test_user.id}, Username={test_user.username}")
        
        # Check folders
        folders = Folder.query.filter_by(owner_id=test_user.id).all()
        print(f"📁 Folders: {len(folders)}")
        for folder in folders:
            print(f"  - {folder.name} (ID: {folder.id}, Parent: {folder.parent_id})")
        
        # Check files
        files = File.query.filter_by(owner_id=test_user.id).all()
        print(f"📄 Files: {len(files)}")
        for file in files:
            print(f"  - {file.filename} (ID: {file.id}, Folder: {file.folder_id})")

if __name__ == '__main__':
    check_test_user() 