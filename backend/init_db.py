from .models import User

def create_test_user(app, db):
    with app.app_context():
        db.create_all()  # Create tables if they don't exist

        # Check if the test user already exists
        test_user = User.query.filter_by(username='testuser').first()
        if not test_user:
            print("Creating test user...")
            new_user = User(username='testuser', email='test@example.com', grade=31)
            new_user.set_password('test')  # Set a secure password
            db.session.add(new_user)
            db.session.commit()
            print("Test user created.")
        else:
            print("Test user already exists.")

def create_admin_and_test_users(app, db):
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
            
        # # Also check if we need to upgrade testuser to admin
        # test_user = User.query.filter_by(username='testuser').first()
        # if test_user and not test_user.is_admin:
        #     print("Upgrading testuser to admin...")
        #     test_user.is_admin = True
        #     db.session.commit()
        #     print("testuser is now an admin!")

        # Check if the test user already exists
        test_user = User.query.filter_by(username='testuser').first()
        if not test_user:
            print("Creating test user...")
            new_user = User(username='testuser', email='test@example.com', grade=31)
            new_user.set_password('test')  # Set a secure password
            db.session.add(new_user)
            db.session.commit()
            print("Test user created.")
        else:
            print("Test user already exists.")

if __name__ == '__main__':
    create_test_user() 