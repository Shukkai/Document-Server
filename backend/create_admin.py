from app import app, db
from models import User

def create_admin_user():
    with app.app_context():
        db.create_all()  # Create tables if they don't exist

        # Check if admin user already exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("Creating admin user...")
            new_admin = User(username='admin', email='admin@example.com', grade=100, is_admin=True)
            new_admin.set_password('admin123')  # Set a secure password
            db.session.add(new_admin)
            db.session.commit()
            print("Admin user created successfully!")
            print("Username: admin")
            print("Password: admin123")
        else:
            print("Admin user already exists.")
            
        # Also check if we need to upgrade testuser to admin
        test_user = User.query.filter_by(username='testuser').first()
        if test_user and not test_user.is_admin:
            print("Upgrading testuser to admin...")
            test_user.is_admin = True
            db.session.commit()
            print("testuser is now an admin!")

if __name__ == '__main__':
    create_admin_user() 