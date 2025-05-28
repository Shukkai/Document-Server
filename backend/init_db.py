from app import app, db  # Assuming your Flask app and db are initialized in app.py
from models import User

def create_test_user():
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

if __name__ == '__main__':
    create_test_user() 